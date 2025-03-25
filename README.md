# Track Course Completion

## Overview
This feature allows tracking of course completion by retrieving user and course details, marking sections, subsections, and units as completed, and setting grades for course subsections.

## Features
- Retrieve user details, course details, course outline, and course subsection grades.
- Mark sections, subsections, and units as completed.
- Set grades for subsections within a course.

## Workflow

### 1. Get Course and User Details
- Submit user email and course ID through a form.
- Retrieve the following details:
  - User details
  - Course details
  - Course outline
  - Course subsection grades

### 2. Mark Course Block as Complete
- Navigate to the course outline.
- Click the "Complete" button on the desired course block.

### 3. Set Grade to Course Subsection
- Navigate to the course grades section.
- Click on the "Set Grades" button for the desired course subsection.
- Confirm the action in the popup window.

---

## Installation Guide

### Step 1: Stop a Running Platform (If Applicable)
```sh
 tutor dev stop
```

### Step 2: Clone the Repository
```sh
git clone https://github.com/Shivahir2003/track_course_complition.git
```

### Step 3: Mount the XBlock
```sh
tutor mounts add <FILE_PATH_TO_DIR>/track_course_complition
```
To confirm the mount, run:
```sh
tutor mounts list
```

### Step 4: Build the Open edX Development Image
```sh
tutor images build openedx-dev
```

### Step 5: Install the Plugin in LMS/CMS Container
1. Open the LMS/CMS container:
   ```sh
   tutor dev run lms bash   # For LMS
   tutor dev run cms bash   # For CMS
   ```
2. Install the XBlock:
   ```sh
   pip install -e <PATH_TO_PLUGIN_IN_CONTAINER>
   ```

