*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${BASE_URL}    http://127.0.0.1:8000
${BROWSER}     Chrome
${USERNAME}    DipeshTest
${FIRSTNAME}   Dipesh
${LASTNAME}    Wagle
${EMAIL}       dipesh@gmail.com
${PHONE}       0420685934
${PASSWORD}    GairidharaNP@1

*** Test Cases ***
Staff Registration
    [Documentation]    Demo of staff registration
    Open Browser    ${BASE_URL}/staffsignup/    ${BROWSER}
    Input Text    id:uname    ${USERNAME}
    Input Text    id:fname    ${FIRSTNAME}
    Input Text    id:lname    ${LASTNAME}
    Input Text    id:email    ${EMAIL}
    Input Text    id:phone    ${PHONE}
    Input Text    id:password   ${PASSWORD}
    Click Button    xpath=//input[@type="submit" and @value="Create"]
    Sleep    2s

Staff Login
    [Documentation]    Open login page, enter credentials, and check dashboard
    Open Browser    ${BASE_URL}/stafflogin/    ${BROWSER}
    Input Text    id:loginuname    ${USERNAME}
    Input Text    id:loginpassword    ${PASSWORD}
    Click Button    xpath=//input[@type="submit" and @value="Login"]
    Wait Until Page Contains    Dashboard    timeout=10s
    Page Should Contain    Dashboard
    Close Browser
