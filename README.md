# Incentive Mechanism App Cluster

This repository contains the source code for an incentive mechanism that chooses between different incentive delivery methods and incentives in an automated manner.

[TOC]

## Prerequisites

Before setting up and running the app, please make sure that:

-   You have **Python** installed. (version >3.8)
-   You have **Poetry** installed.

## Manual execution

To run agatha manually:

1. Install dependencies with `poetry install`
2. Run with `poetry run uvicorn agatha.main:agatha --reload --port 5442`

To reset the database and run agatha in development mode use `reset_db_run_dev.sh`

## Automated execution

Execute the run script in `executables` with `python`:

```
python executables/run-agatha.py
```

## Manual Testing

### Run Script Test

| Precondition          | Operation                                                | Expected Output                  |
| --------------------- | -------------------------------------------------------- | -------------------------------- |
| Virtual env activated | Run run-agatha.py with `--dev` and go to endpoint `/`    | "Incentive mechanism is running" |
|                       | Run run-agatha.py without `--dev` and go to endpoint `/` | Homepage with apps and APIs      |

### Configuration App Authorization

| Env  | Precondition                                         | Operation                          | Expected Behavior                                                 |
| ---- | ---------------------------------------------------- | ---------------------------------- | ----------------------------------------------------------------- |
| prod | No existed cookie, e.g. incognito mode or logged out | Try enter `/app/config/mechanisms` | Bounced back to login page                                        |
|      |                                                      | Login with `user@example.com`      | Redirected to error page with `403`                               |
|      |                                                      | Login with `demo@example.com`      | Redirected to `/app/config/employees`, email displayed on nav bar |
|      | Already logged in with admin email                   | Click `Logout` on the nav bar      | Redirected to login page                                          |
|      | Just logged out                                      | Try enter `/app/config/mechanisms` | Bounced back to login page                                        |
| dev  |                                                      | Access any config app url          | Logged in as `demo@example.com`, no logout button                 |

### Configuration App Functionality

| Functionality                             | Operation                                                             | Expected Behavior                                                                          |
| ----------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Edit employee configuration               | Click on `Configure` of an employee                                   | An edit popup is opened, with options pre-selected to the employee's current configuration |
|                                           | Click on either dropdowns                                             | All available delivery models or incentive types are displayed                             |
|                                           | Change the configuration and click `Confirm`                          | Edit popup is closed, employee configuration changed in the overview                       |
| Add new delivery model or incentive type  | Click `Add New xxx`                                                   | An edit popup is opened                                                                    |
|                                           | Do not fill in anything, click `Create xxx`                           | "Please fill out this field" hint on the Name field                                        |
|                                           | Input a valid name and click `Create xxx`                             | Edit popup is closed, delivery model or incentive type added                               |
|                                           | Try adding another one with a duplicated name                         | Redirected to the 409 Conflict Error Page                                                  |
| Edit new delivery model or incentive type | Click `Edit` button on an item                                        | Edit popup is opened, text fields prefilled                                                |
|                                           | Form validation tests are the same as "add" functionality tests above |                                                                                            |

### Survey App Functionality

| Precondition                                                                                                                                       | Operation                                                         | Expected Behavior                                                                                                                                                         |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A complete survey with questions that cover both delivery model and incentive type is already in database                                          | Go to endpoint `/app/survey/{survey_id}/{random_uid}`             | Survey opened and only one question is showing. Next button showing in the bottom right corner is disabled. Previous button showing in the bottom left corner is disabled |
| At any time during the survey                                                                                                                      |                                                                   | At most 1 unanswered question is showing                                                                                                                                  |
| No question is answered                                                                                                                            |                                                                   | Progress bar is empty / not showing                                                                                                                                       |
|                                                                                                                                                    | Answer a questions for the first time                             | Progress bar moves forward (same amount for each question)                                                                                                                |
|                                                                                                                                                    | Answer an already answered question                               | Progress bar does not change                                                                                                                                              |
| All but one question is answered                                                                                                                   | Answer the last question                                          | The progress bar is full. The next button is not showing. The submit button is showing and enabled                                                                        |
| A likert question is showing                                                                                                                       | Hover over an answer option                                       | The answer choice gets highlighted while the curser hovers above the choice                                                                                               |
| An unanswered likert question is showing                                                                                                           | Click on an answer option                                         | The answer choice gets permanently highlighted. The question gets answered (see cases with Operation "Answer the question" below)                                         |
| An unanswered text question is showing                                                                                                             | Click on the textfield                                            | The question gets answered (see cases with Operation "Answer the question" below)                                                                                         |
| An unanswered question is showing and the pagination limit not reached (<= 2 questions showing) and there is at least one more unanswered question | Answer the question                                               | The next unanswered question appears                                                                                                                                      |
| An unanswered question is showing and the pagination limit is reached (3 questions showing) and there is at least one more unanswered question     | Answer the question                                               | The next button gets enabled                                                                                                                                              |
| An unanswered question is showing                                                                                                                  |                                                                   | The next button is disabled                                                                                                                                               |
| The next button is enabled                                                                                                                         | Click the next button                                             | All current questions disappear and the next page of (potentially already answered) questions is shown                                                                    |
| The previous button is enabled                                                                                                                     | Click the previous button                                         | The previous page of already answered questions is shown. The next button is enabled                                                                                      |
| The submit button is showing                                                                                                                       | Click the submit button                                           | All questions get hidden and the website shows that the answers have been submitted. The web server logs (at level debug) all answers as given by the user                |
|                                                                                                                                                    | Submit the survey and go to endpoint `/incentives/{random_uid}`   | Calculated configuration returned                                                                                                                                         |
| Survey for given user is already filled out                                                                                                        | Go to survey endpoint with the same survey id and random id again | Display error message: survey already completed                                                                                                                           |
| The same survey is already completed in another tab                                                                                                | Submit it again                                                   | Shows "something went wrong"                                                                                                                                              |
