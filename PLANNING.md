# Project background
This is a learning platform. 
Instructors are allowed to create courses, and they can also use AI to develop new mini-courses by inputting their own topics, requirements, levels, and teaching content, and refining learning content and activities. Instructors should be able to customize (manually or using AI) the learning contents and activities of the existing mini-courses. The instrcutors can choose to add their students in the courses. Instructors can only see the courses that are created by their own.
For students, they should be able to see their enrolled courses, and they should be able to review scores of each level, allow retrying the modules, users can also generate their
own topics and path for self-learning. 
For admins, they should see all the available courses on the platform. In each course, admins can see the instructor, content, students. Admins have rights to open or lock a course, and add or remove a student. Admins can also create accounts for instructor and students. Initially, set admin username and password as "admin" and "password" respectively.

# Architecture
The landing page should show swipe up animation showing "learning platform", then ask user to login as admin, instructor, student.
The content menu should be on the left. Top right corner should have a profile. Inside profile included settings, and logout function.
Use openrouter nvidia/nemotron-3.5-lightning:free model as the model behind for instructors and students to generate content. Generate a prompt store in prompts/content_prompt.md for generating content. Use the openrouter API key in .env
Allow users to upload .pdf, .pptx, .doc for creating content.
When there is any changes made by the instructor, students and admins should also see the changes on their page.
This app will use neon database, get the database URL in .env
This app will be deployed to vercel eventually. Avoid creating codes that would conflict with deploying to vercel. 