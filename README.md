OVERVIEW - CVT Project by Moldovan Luca

This repository presents the essential project backbone and its core functionalities for demonstration purposes; it is not the official code used in production.

1) PROJECT STRUCTURE

                                                            The web interface
                                                                    ^
                                                                    |
                                                                    |
                                                                    |
                                                                    |
Input file for C ------> C program -----> outputfile from C ---- > FLASK <-------> SQLite database
                          



2) First Steps into the Project

a) Initial Research

-Flask for building the web application.

-Databases, focusing on SQLite and SQL syntax for data storage and manipulation.

-Python programming fundamentals, particularly how it interfaces with other components.

-Linux subsystems, which helped me understand the runtime environment better.

b) Early Attempts

I didn’t begin directly with this project. Initially, I created several test projects that were somewhat messy and experimental. These served as sandboxes to try out ideas and understand how various components might interact, particularly:

-Integrating a C/C++ program into a Python workflow

-Using Flask 

-Interacting with a SQLite database

c) Starting the Main Project

-First, I wrote a Python script to initialize the SQLite database

-Then, I created an accompanying SQL script to define and create the necessary table structure within the database.

-One of the most challenging parts was designing the web interface. Unlike my previous test app, which simply displayed "username - email" pairs, this project aimed to resemble a task manager, requiring a more structured and interactive UI that communicates the application's purpose clearly.

3) How Everything Works

a) Overview

-The application is a Flask-based web app that integrates a C program, processes its output, stores it in an SQLite database, and then displays that data on a web interface.

b) How It All Comes Together

-The Python Flask app serves as a middle man

-Upon execution (python the_app.py), the Flask server:

-Automatically runs the C program (I wrote a script for this because I wanted the app to act like a real app everything to be in one unit, not requiring to compile each file by hand) 

-Collects the output from the C program.

-Parses and stores this data into the SQLite database.

-Renders this information on a web-based user interface.

This creates a self-contained application, simulating how a real-world task manager or data visualization tool would work. The automation of the C program's execution within the Flask environment enhances usability and streamlines the workflow, making the whole project act like a cohesive software product rather than a disjointed collection of scripts. 
