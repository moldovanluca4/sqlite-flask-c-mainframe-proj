#include <stddef.h>                                                      //this is a short demonstration how to acces the communication vector table (cvt) on an IBM mainframe running on z/os
#include <stdio.h>                                                       //we assume we have all the right environments and priviliges and of course acces to a mainframe


void *get_cvt(){                                                         //the function basically returns a pointer which is pointing to the real memory addres of the cvt 0x10 
    void *cvt_pointer = (void*)0x10;                                     //we save the constant address into the pointer (0x10 decimal 16)

    return cvt_pointer;                                                  //in z/os i think the cvt always starts at 0x10 memory address
}                                                                        //the last step will be to return the pointer       

//we are not doing something really complicated we just return the pointer to a known memory address


int main(){                                                                                                                           
    void *cvt = get_cvt();                                                  //we call the function into the main and we print the address using %p bcs we are printing a pointer


    printf("Memory addres of the cvt: %p \n", cvt);

    return 0;
}

//to get this program on the mainframe we must follow some steps - environment(acces to ibm z/os mainframe, program must be secure, we need special compilers for C/C++, be able to submit jcl jobs same as with cobol)
// -authorization (the memory address we want is a physical one not a virtual one, so it is saved in a prefixed area thats why it is known to be 0x10, this area is protected even for reading so with no authorization the program can lead into failures like memory leak or segmentation problems/fault : for ex we try to read what is in there and we will receive only a black screen or a crash)
// -one we completed what was before we need to compile somehow the program, for this we use jcl 
