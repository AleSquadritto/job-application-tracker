#AI Usage Documentation

#Tools Used 
- Claude for debugging, Flask routes, and help with HTML frontend

#Key Prompts
- (password for MySQL wasn't working for some reason) *attached screenshot* "Help me understand why it's giving me this error and help me reset the password"
- I attached screenshots of the project specification and asked: "Walk me through the Flask Routes and HTML and help me with future code snippets I attach of this" 
- "Using this rubric, check that I have completed everything"
- "Help me with the HTML templates and the style.css" since I don't have much experience with HTML, AI helped me with the frontend aspect of this project. 
- "My app isn't running, why?" (I attached my initial code)
- "Error code: 1064 ... near... Don't give me the solution, tell me where I went wrong" (I had put as notes FK -> companies, as shown in the specification, and forgot that I needed to write the FOREIGN KEY line. It promptly pointed out my mistake and I wrote the solution myself).

#What Worked Well
- It showed me how everything connected to the rubric (except the README and AI Usage since I hadn't done that yet) and what I had missed/completed.
- Since I asked for explanations of the code, it did just that after I asked for help whenever I was stuck or my code had a bug (for example in the app.py, I had missed extra quotation marks).
- It helped me create the CRUD tables and connecting them to the dashboard and Job Match, something I was struggling with (in app.py).
- the code in database.py is similar to what we did in assignment 5 so I could read and understand what AI helped me generate and see how all the routes in app.py got its information from MySQL. 


#What I modified
- When I showed it my SQL schema it added extra restrictions, so I removed those and asked for clarity as to why they were needed/why it addem them, many didn't make sense but I kept the ON DELETE CASCADE
- It created sample data that modified the schema tables, so I went off of what we had done in past assignments. And utilized that as a base for the AI to go off, especially for the interview_data, links, and requirements
- When asking for help with the templates, claude created 3 extra files, so I saw what it had created asked why, and condensed them into what was shown in the project specification.
- some of the style.css was useless or I didn't like how it looked so I modified it. 


#Lessons Learned
- I learned that AI code needs to be tested and checked
- Sometimes it added extra steps or made up things that didn't exist so when used I need to make sure that I know exactly what it's doing
- Attaching code snippets and asking for clarifications/explanations or what I can do better helped me learn and understand everything better.
- When shown things without context it can cause more damage than help, so I need to be careful with my prompts