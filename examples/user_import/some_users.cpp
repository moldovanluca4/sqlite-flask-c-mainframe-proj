#include <fstream>
#include <iostream>
#include <string>

using namespace std;

static void write_csv_field(ostream& out, const string& value) {
    out << '"';
    for (char ch : value) {
        if (ch == '"') out << '"';
        out << ch;
    }
    out << '"';
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        cerr << "Usage: ./some_users <input-file> <output-csv>\n";
        return 1;
    }

    ifstream in(argv[1]);
    if (!in) {
        cerr << "Failed to open input file\n";
        return 2;
    }
    ofstream out(argv[2]);
    if (!out) {
        cerr << "Failed to open output file\n";
        return 2;
    }

    string name, email;
    while (in >> name) {
        if (!(in >> email)) {
            cerr << "Each input row must contain a name and email\n";
            return 3;
        }
        write_csv_field(out, name);
        out << ',';
        write_csv_field(out, email);
        out << '\n';
    }
    out.close();
    return in.bad() || !out ? 2 : 0;
}
