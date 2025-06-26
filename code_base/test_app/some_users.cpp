#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

using namespace std;

int main(int argc, char* argv[]) {
    if (argc != 3) {
        cerr << "Usage: ./some_users <input_users_for_cpp.txt> <output_users_file.csv>\n";
        return 1;
    }

    ifstream in(argv[1]);
    ofstream out(argv[2]);

    if(!in){
        cerr<<"Failed to open input file "<<endl;
        return 2;
    } else if(!out){
        cerr<<"error ouput";
        return 2;
    }

    string name, email;
    while (in >> name >> email){
        out << name << ',' << email << '\n';   
    }
    return 0;
}
