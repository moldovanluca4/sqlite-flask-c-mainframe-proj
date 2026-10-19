#include <ctype.h>
#include <errno.h>
#include <stdint.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/wait.h>
#include <unistd.h>

typedef struct {
    uint32_t cvtdate;
    void *ecvt;
} CVT;

static CVT fake_cvt = {
    .cvtdate = 0x0007D0B1,
    .ecvt = (void *)(uintptr_t)0x7FFBCAFE
};

static void decode_cvtdate(uint32_t raw, int *year, int *yday) {
    uint32_t date = raw & 0x0FFFFFFF;
    int yy = (date >> 12) & 0xFF;
    *year = (yy < 70) ? yy + 2000 : yy + 1900;
    *yday = date & 0xFFF;
}

static char *trim(char *text) {
    while (*text && isspace((unsigned char)*text)) text++;
    char *end = text + strlen(text);
    while (end > text && isspace((unsigned char)*(end - 1))) end--;
    *end = '\0';
    return text;
}

static void write_csv_text(FILE *out, const char *text) {
    for (; *text; text++) {
        if (*text == '"') fputc('"', out);
        fputc(*text, out);
    }
}

static int write_tasks(FILE *out, const char *ps_command) {
    int descriptors[2];
    if (pipe(descriptors) != 0) return 1;
    posix_spawn_file_actions_t actions;
    if (posix_spawn_file_actions_init(&actions) != 0) {
        close(descriptors[0]);
        close(descriptors[1]);
        return 1;
    }
    int setup = posix_spawn_file_actions_adddup2(&actions, descriptors[1], STDOUT_FILENO);
    if (setup == 0) setup = posix_spawn_file_actions_addclose(&actions, descriptors[0]);
    if (setup == 0) setup = posix_spawn_file_actions_addclose(&actions, descriptors[1]);
    pid_t child;
    char *arguments[] = {(char *)ps_command, "-eo", "comm", "--no-headers", NULL};
    extern char **environ;
    int spawned = setup == 0
        ? posix_spawn(&child, ps_command, &actions, NULL, arguments, environ) : setup;
    posix_spawn_file_actions_destroy(&actions);
    if (spawned != 0) {
        close(descriptors[0]);
        close(descriptors[1]);
        return 1;
    }
    close(descriptors[1]);
    FILE *processes = fdopen(descriptors[0], "r");
    if (!processes) close(descriptors[0]);
    if (!processes) {
        while (waitpid(child, NULL, 0) < 0 && errno == EINTR) {}
        return 1;
    }

    fputs("TASKS,\"", out);
    char buffer[512];
    int first = 1;
    while (fgets(buffer, sizeof buffer, processes)) {
        char *task = trim(buffer);
        if (!*task) continue;
        if (!first) fputs("; ", out);
        write_csv_text(out, task);
        first = 0;
    }
    int read_failed = ferror(processes);
    int close_failed = fclose(processes);
    int status;
    pid_t waited;
    do {
        waited = waitpid(child, &status, 0);
    } while (waited < 0 && errno == EINTR);
    if (read_failed || close_failed != 0 || waited < 0 || !WIFEXITED(status)
        || WEXITSTATUS(status) != 0) {
        fputs("Process collection failed\n", stderr);
        return 1;
    }
    if (first) fputs("No processes found", out);
    fputs("\"\n", out);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <input-file> <output-csv> <ps-executable>\n", argv[0]);
        return 1;
    }
    FILE *in = fopen(argv[1], "r");
    if (!in) {
        perror("Cannot open input file");
        return 2;
    }
    FILE *out = fopen(argv[2], "w");
    if (!out) {
        perror("Cannot open output file");
        fclose(in);
        return 2;
    }

    int year, yday;
    decode_cvtdate(fake_cvt.cvtdate, &year, &yday);
    fputs("field,value\n", out);
    char line[128];
    int status = 0;
    while (fgets(line, sizeof line, in)) {
        char *field = trim(line);
        if (!*field || *field == '#') continue;
        if (strcasecmp(field, "CVTDATE") == 0) {
            fprintf(out, "CVTDATE,%04d-%03d\n", year, yday);
        } else if (strcasecmp(field, "CVTADDR") == 0) {
            fprintf(out, "CVTADDR,%p\n", (void *)&fake_cvt);
        } else if (strcasecmp(field, "ECVT") == 0) {
            fprintf(out, "ECVT,%p\n", fake_cvt.ecvt);
        } else if (strcasecmp(field, "TASKS") == 0) {
            if (write_tasks(out, argv[3]) != 0) {
                status = 3;
                break;
            }
        } else {
            fputc('"', out);
            write_csv_text(out, field);
            fputs("\",UNKNOWN\n", out);
        }
    }
    if (ferror(in) || ferror(out)) status = 2;
    if (fclose(in) != 0) status = 2;
    if (fclose(out) != 0) status = 2;
    return status;
}
