#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <ctype.h>


//we define a fake cvt strcuture 

typedef struct {
    uint32_t cvtdate;                                                      //we define a 32 bit encoded cvt date
    void *ecvt;                                                            //a pointer to the enxtended cvt also a fake ecvt
} CVT;                                                                      //in this way we read from the system control block or the kernel this may be more used in the OS development


//the coded cvt values

static CVT fake_cvt = {
    .cvtdate = 0x0007D0B1,                                                  //date is encoded as 2025 day 177
    .ecvt = (void*)0x7FFBCAFE                                               //this is some dummy data to stimulate real OS situations this is good for testing and also integration with flask, so the connection between C and python                                
};



//returning the pointer to the fake cvt

static inline CVT *get_CVT(void) {
    return &fake_cvt;
}


//we decode the cvt date or acces date

static void decode_cvtdate(uint32_t raw, int *year, int *yday) {          //we extract the year and day of the year encoded in cvtdate
    uint32_t d = raw & 0x0FFFFFFF;                                        
    int yy = (d >> 12) & 0xFF;                                             //extract the 8 bit year
    *year = (yy < 70) ? yy + 2000 : yy + 1900;                             //if the yy < 70 than the year is 2000+ and if the yy > 70 year is 1900+
    *yday = d & 0xFFF;                                                     //we get the day of the year here
}                                                                          //we encoded the year and day of the year in a 32 bit format jsut bsc this is really common in a low level C program like this one should have been because it works closely to the memory of the computer/mainframe


//string trimmer helper

static char *trim(char *s) {                                               //nothing too complicated we find a white space, tabs or newlines we remove them
    while (*s && isspace((unsigned char)*s)) s++;
    char *end = s + strlen(s);
    while (end > s && isspace((unsigned char)*(end - 1))) end--;           
    *end = '\0';
    return s;                                                               //good way to avoid errors and also the errors regarding external files can be pretty confusing cause computer see different things than us humans
}




int main(int argc, char **argv) {

    FILE *in = fopen(argv[1], "r");                                        //we open our files. input file for reading and output file for writing
    FILE *out = fopen(argv[2], "w");
    if (!in || !out) {                                                     //we have to check if we could open the files
        perror("Cannot open input or output file");
        return 2;
    }

    CVT *cvt = get_CVT();         
    int year, yday;
    decode_cvtdate(cvt->cvtdate, &year, &yday);

    fprintf(out, "field,value\n");                                          //this line here is important for the python method dictreader to be able to parse easily the output

    char line[128];

    while (fgets(line, sizeof line, in)) {                                 //processing loop. reads each line of the input, trims whitespaces, we skip empty lines or any comment lines, and checks for the corner cases for the know directives
        char *field = trim(line);
        if (*field == '\0' || *field == '#') continue;

        if (strcasecmp(field, "CVTDATE") == 0) {
            fprintf(out, "CVTDATE,%04d-%03d\n", year, yday);              //encodes cvtdate
        } else if (strcasecmp(field, "CVTADDR") == 0) {
            fprintf(out, "CVTADDR,%p\n", (void *)cvt);                    //writes the memory addres of the fake cvt
        } else if (strcasecmp(field, "ECVT") == 0) {
            fprintf(out, "ECVT,%p\n", cvt->ecvt);                         //prints the memory address of the ecvt pointer inside the cvt
        } else if (strcasecmp(field, "TASKS") == 0) {
            const char *cmd = "ps -eo comm --no-headers";                 //we run a shell command to see what activity we have on the laptop running processes or any other apps

            FILE *fp = popen(cmd, "r");                                   //what we stored in the cmd pointer we make a string so all the processes running are separeted by a semi colon this is good for when we going to see them in the web interface
            if (fp) {
                char buffer[512];
                char all_tasks[4096] = {0};
                int first = 1;
                while (fgets(buffer, sizeof buffer, fp)) {                 //for example in here if we would had a C program that uses a command to see what is running on Windows for example we could specify to form the string and the output with only the processes which contain only ".exe" in that manner we would see only the apps running
                    char *task = trim(buffer);
                    if (*task) {
                        if (!first) strcat(all_tasks, "; ");
                        strcat(all_tasks, task);
                        first = 0;
                    }
                }
                pclose(fp);
                if (strlen(all_tasks) > 0) {
                    fprintf(out, "TASKS,%s\n", all_tasks);
                } else {
                    fprintf(out, "TASKS,No processes found\n");
                }
            } else {
                fprintf(out, "TASKS,Task fetch failed\n");
            }
        } else {
            fprintf(out, "%s,UNKNOWN\n", field);                            //this occurs when we dont know what input we have and logs anyway outputing unknown this is good for avoiding crashes or any other bugs and overall good for debugging
        } 
    }

    fclose(in);                                                            //and last step closing the files 
    fclose(out);
    return 0;
}


//the input file we have the - CVTDATE which extracts and prints a date encoded in the fake CVT struct
                          // - CVTADDR prints the memory address of the fake CVT structure
                          // - ECVT prints the memory address stored in th ecvt pointer and then is hardcoded
                          // - TASKS we execute the linux command to collect all the runing processes names

//imagine that the input file is like a script telling the C program what data to extract and write out
//so each of the lines presented in the input file is a command for the program
//we also specify in the program that we want to print in the output file field, value
//the input acts like a list for the C program reads line by line and decides what output to generate



//we have a fake cvt memory address => then whose address do we see on the output?
//the cvt struct is not an actual communication vector table like the one on a mainframe so is fake , in truth is just a local variable
//memory address printed by CVTADDR is the real runtime memory address of fake_cvt bcs is allocated by the programs data segment
//the real memory address of the cvt in an ibm mainframe is 0x10
//so in conclusion fake_cvt is the actual memory address in RAM at runtie where the fake cvt struct is located
//even though the data inside fake_cvt is a fake address the same logic applies also on a mainfram . the pointer we print is real bcs the struct exist in memory during the execution of the program