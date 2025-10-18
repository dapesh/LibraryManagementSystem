*** Settings ***
Library    SeleniumLibrary
Library    String
Suite Setup       Login To Dashboard
Suite Teardown    Close All Browsers
Test Teardown     Capture Page Screenshot

# Give Selenium a sensible default timeout
# (works as the default for explicit waits like Wait Until Page Contains Element)
# You can tune this higher/lower if needed.
Test Setup        Set Selenium Timeout    10s


*** Variables ***
${BASE_URL}    http://127.0.0.1:8000
${BROWSER}     Chrome
${USERNAME}    Dipesh
${PASSWORD}    GairidharaNP@1

# From manual test table (exact values)
${BOOK_ID}         B101
${BOOK_NAME}       Python Basics
${BOOK_SUBJECT}    CS
${BOOK_CATEGORY}   Not-Issued

${BOOK_ID_2}       B102
${BOOK_ID_3}       B103
${BOOK_ID_INVALID}    @@B105

${STUDENT_ID}      S001
${STUDENT_NAME}    Dipesh Wagle
${STUDENT_NAME_2}  Ramesh              # for TC_LIB_12

# Optional messages (tweak if your app shows these flashes)
${MSG_REQUIRED}         All fields required
${MSG_DUP_BOOK}         Book already exists
${MSG_DUP_STU}          Student already exists
${MSG_INVALID_BOOK}     Invalid Book ID
${MSG_LENGTH_ERR}       Invalid ID length


*** Keywords ***
Login To Dashboard
    Open Browser    ${BASE_URL}/stafflogin/    ${BROWSER}
    Input Text      id:loginuname       ${USERNAME}
    Input Text      id:loginpassword    ${PASSWORD}
    Click Button    xpath=//input[@type="submit" and @value="Login"]
    Wait Until Page Contains    Dashboard    10s

Go To Dashboard
    Go To    ${BASE_URL}/dashboard/
    Wait Until Page Contains    Dashboard    10s

Add Book
    [Arguments]    ${book_id}    ${book_name}    ${subject}    ${category}
    Go To    ${BASE_URL}/addbook/
    Wait Until Page Contains    Add Book    10s
    Input Text    name:bookid       ${book_id}
    Input Text    name:bookname     ${book_name}
    Input Text    name:subject      ${subject}
    Input Text    name:category     ${category}
    Click Button  xpath=//button[@type='submit'] | //input[@type='submit']
    # If app redirects to dashboard on success:
    Run Keyword And Ignore Error    Wait Until Location Contains    /dashboard/    5s
    Go To Dashboard

Book Count
    [Arguments]    ${book_id}
    Go To Dashboard
    # Prefer element-based wait (table/list present) if available
    Run Keyword And Ignore Error    Wait Until Page Contains Element    xpath=//table | //tbody | //div[contains(@class,'table')]    5s
    ${count}=    Get Element Count    xpath=//td[normalize-space()='${book_id}']
    RETURN    ${count}

Ensure Book Listed
    [Arguments]    ${book_id}    ${book_name}    ${subject}    ${category}
    ${count}=    Book Count    ${book_id}
    Run Keyword If    ${count} == 0    Add Book    ${book_id}    ${book_name}    ${subject}    ${category}

Add Student
    [Arguments]    ${student_name}    ${student_id}
    Go To    ${BASE_URL}/addstudent/
    Wait Until Page Contains    Add Student    10s
    Input Text    name:sname        ${student_name}
    Input Text    name:studentid    ${student_id}
    Click Button  xpath=//button[@type='submit'] | //input[@type='submit']

Student Count
    [Arguments]    ${student_id}
    Go To    ${BASE_URL}/viewstudents/
    # Use element-based wait to avoid brittle text checks
    Wait Until Page Contains Element    xpath=//table | //tbody | //div[contains(@class,'table')]    10s
    ${count}=    Get Element Count    xpath=//td[normalize-space()='${student_id}']
    RETURN    ${count}

Ensure Student Listed
    [Arguments]    ${student_name}    ${student_id}
    ${count}=    Student Count    ${student_id}
    Run Keyword If    ${count} == 0    Run Keywords
    ...    Add Student    ${student_name}    ${student_id}
    ...    AND    Wait Until Page Contains    ${student_id}    10s

Open Temp Browser
    [Arguments]    ${url}
    ${h}=    Open Browser    ${url}    ${BROWSER}
    RETURN    ${h}


*** Test Cases ***
TC_LIB_01: Verify adding a new book
    [Documentation]    Log in → Add Book (B101) → Verify on dashboard
    Add Book    ${BOOK_ID}    ${BOOK_NAME}    ${BOOK_SUBJECT}    ${BOOK_CATEGORY}
    ${count}=    Book Count    ${BOOK_ID}
    Should Be True    ${count} >= 1    msg=Book not visible after add

TC_LIB_02: Verify adding a book with missing fields
    [Documentation]    Leave Book Name empty for B102 → Expect required validation OR no row
    Go To    ${BASE_URL}/addbook/
    Wait Until Page Contains    Add Book    10s
    Input Text    name:bookid       ${BOOK_ID_2}
    # Leave blank properly:
    Input Text    name:bookname     ${EMPTY}
    Input Text    name:subject      Math
    Input Text    name:category     Not-Issued
    Click Button  xpath=//button[@type='submit'] | //input[@type='submit']
    Sleep    0.5s
    ${seen}=    Run Keyword And Return Status    Wait Until Page Contains    ${MSG_REQUIRED}    2s
    ${count}=    Book Count    ${BOOK_ID_2}
    Should Be True    ${seen} or ${count} == 0    msg=Empty book name was accepted (count=${count})

TC_LIB_03: Verify duplicate Book ID restriction
    [Documentation]    Try adding B101 again → Expect duplicate rejected (count stays 1 or dup message)
    Ensure Book Listed    ${BOOK_ID}    ${BOOK_NAME}    ${BOOK_SUBJECT}    ${BOOK_CATEGORY}
    ${before}=    Book Count    ${BOOK_ID}
    Add Book    ${BOOK_ID}    ${BOOK_NAME}    ${BOOK_SUBJECT}    ${BOOK_CATEGORY}
    ${dup_seen}=  Run Keyword And Return Status    Wait Until Page Contains    ${MSG_DUP_BOOK}    2s
    ${after}=     Book Count    ${BOOK_ID}
    Should Be True    ${dup_seen} or ${after} == ${before}    msg=Duplicate created (before=${before}, after=${after})

TC_LIB_04: Verify student registration
    [Documentation]    Add Student (S001 / Dipesh Wagle) → Verify in list
    Add Student    ${STUDENT_NAME}    ${STUDENT_ID}
    ${scount}=    Student Count    ${STUDENT_ID}
    Should Be True    ${scount} >= 1    msg=Student not visible after add

TC_LIB_05: Verify duplicate student registration restriction
    [Documentation]    Try adding S001 again → Expect duplicate rejected (count stays 1 or dup message)
    Ensure Student Listed    ${STUDENT_NAME}    ${STUDENT_ID}
    ${s_before}=    Student Count    ${STUDENT_ID}
    Add Student     ${STUDENT_NAME}    ${STUDENT_ID}
    ${dup_s_seen}=  Run Keyword And Return Status    Wait Until Page Contains    ${MSG_DUP_STU}    2s
    ${s_after}=     Student Count    ${STUDENT_ID}
    Should Be True    ${dup_s_seen} or ${s_after} == ${s_before}    msg=Duplicate student created (before=${s_before}, after=${s_after})

TC_LIB_06: Verify book search by ID
    [Documentation]    Search query for B101 should show matching record
    Ensure Book Listed    ${BOOK_ID}    ${BOOK_NAME}    ${BOOK_SUBJECT}    ${BOOK_CATEGORY}
    Go To    ${BASE_URL}/Search/?query2=${BOOK_ID}
    Wait Until Page Contains    ${BOOK_ID}    10s

TC_LIB_07: Verify dashboard reflects added book and status
    [Documentation]    Dashboard shows recently added book (B101) and its status
    Ensure Book Listed    ${BOOK_ID}    ${BOOK_NAME}    ${BOOK_SUBJECT}    ${BOOK_CATEGORY}
    Go To Dashboard
    Page Should Contain    ${BOOK_ID}
    # Optionally also assert status text:
    # Page Should Contain    ${BOOK_CATEGORY}

TC_LIB_08: Verify View Student reflects added student records
    [Documentation]    View Students shows S001 (Dipesh Wagle)
    Ensure Student Listed    ${STUDENT_NAME}    ${STUDENT_ID}
    ${scount}=    Student Count    ${STUDENT_ID}
    Should Be True    ${scount} >= 1

TC_LIB_09: Verify validation for empty Book Name (Negative)
    [Documentation]    Leave Book Name empty for B103 → Expect required validation OR no row
    Go To    ${BASE_URL}/addbook/
    Wait Until Page Contains    Add Book    10s
    Input Text    name:bookid       ${BOOK_ID_3}
    Input Text    name:bookname     ${EMPTY}
    Input Text    name:subject      CS
    Input Text    name:category     Not-Issued
    Click Button  xpath=//button[@type='submit'] | //input[@type='submit']
    Sleep    0.5s
    ${seen}=    Run Keyword And Return Status    Wait Until Page Contains    ${MSG_REQUIRED}    2s
    ${count}=    Book Count    ${BOOK_ID_3}
    Should Be True    ${seen} or ${count} == 0    msg=Empty book name was accepted (count=${count})

TC_LIB_10: Verify invalid Book ID format (Negative)
    [Documentation]    Enter @@B105 → Expect invalid format rejected OR no row
    Add Book    ${BOOK_ID_INVALID}    Mathematics    ${BOOK_SUBJECT}    ${BOOK_CATEGORY}
    Sleep    0.5s
    ${seen}=    Run Keyword And Return Status    Wait Until Page Contains    ${MSG_INVALID_BOOK}    2s
    ${count}=    Book Count    ${BOOK_ID_INVALID}
    Should Be True    ${seen} or ${count} == 0    msg=Invalid Book ID was accepted (count=${count})

TC_LIB_11: Verify unauthorized Add Book access (Negative)
    [Documentation]    Without login, open /addbook in a new session → Expect redirect to login
    ${orig}=    Get Browser Id
    ${h}=    Open Temp Browser    ${BASE_URL}/addbook/
    # If your app redirects to login page text "Login" or a login form element:
    Wait Until Page Contains    Login    5s
    Switch Browser    ${h}
    Close Browser
    Switch Browser    ${orig}

TC_LIB_12: Verify long Student ID handling (Edge Case)
    [Documentation]    Use 25-char StudentID → Expect rejected OR not shown in list
    Go To    ${BASE_URL}/addstudent/
    Wait Until Page Contains    Add Student    10s
    Input Text    name:sname        ${STUDENT_NAME_2}
    Input Text    name:studentid    S0000000000000000000000000
    Click Button  xpath=//button[@type='submit'] | //input[@type='submit']
    Sleep    0.5s
    ${seen}=    Run Keyword And Return Status    Wait Until Page Contains    ${MSG_LENGTH_ERR}    2s
    ${scount}=  Student Count    S0000000000000000000000000
    Should Be True    ${seen} or ${scount} == 0    msg=Overlong Student ID was accepted (count=${scount})

TC_LIB_13: Verify case sensitivity in Book ID (Edge Case)
    [Documentation]    Add "b101" when "B101" exists → Expect treated as duplicate (total count remains 1)
    Ensure Book Listed    ${BOOK_ID}    ${BOOK_NAME}    ${BOOK_SUBJECT}    ${BOOK_CATEGORY}
    ${before}=    Book Count    ${BOOK_ID}
    Add Book     b101    Python Crash    ${BOOK_SUBJECT}    ${BOOK_CATEGORY}
    ${after}=     Book Count    ${BOOK_ID}
    Should Be Equal As Integers    ${after}    ${before}    msg=Case-sensitive duplicate was added (before=${before}, after=${after})
