// useful snippets
// chrome.exe --user-data-dir="C:/Chrome dev session" --disable-web-security

function uploadfile() {
    console.log("uploadfile main function called")
    /* Check file exist and call for temporary signature */
    const files = document.getElementById('picture').files;
    const file = files[0];
    if (!file) {
        return;
    }
    getSignedRequest(file);
    /* Function to get the signature from the flask app */
    function getSignedRequest(file) {
        console.log('Getting Signed request')
        const xhttp = new XMLHttpRequest();
        //xhr.open('GET',`/sign-s3/?file-name=${file.name}&file-type=${file.type}`);
        xhttp.onreadystatechange = function () {
            console.log('ppReg: ' + this.readyState + " " + this.status)
            if (this.readyState == 4 && this.status == 200) {
                const response = JSON.parse(this.responseText);
                console.log(this.readyState, this.status)
                uploadFile(file, response.data, response.url);
            }
        };
        xhttp.open('GET', `/s3Request/?file-name=${file.name}&file-type=${file.type}`);
        xhttp.send();
        console.log('ppReg Sent to Flask')

        // xhr.send();
    }
    /* Function to send the file to S3 */
    function uploadFile(file, s3Data, url) {

        console.log('uploading file after ppReq')
        const xreq = new XMLHttpRequest();

        xreq.onreadystatechange = function () {
            console.log('s3Upload: ' + this.readyState + " " + this.status)
            if (this.readyState == 4 && this.status == 204) {
                //const response = JSON.parse(this.responseText);
                //uploadFile(file,response.data,response.url);
                console.log('File upload received by s3')

            }
            // else if (this.readyState == 4 && this.status != 204) {
            //     alert("File upload failed.")

            else {
                // change to alert
                console.log(this.readyState, this.status)
            }
        };
        xreq.open('POST', s3Data.url, true); // set to false but need to change.
        xreq.setRequestHeader('x-amz-acl', 'public-read');
        const postData = new FormData();
        for (key in s3Data.fields) {
            postData.append(key, s3Data.fields[key]);
        }
        postData.append('file', file);
        console.log(postData)
        xreq.send(postData)
        console.log('Data Sent!')
        
    }
}
// ********************** WORKS *********************
// document.getElementById("accountForm").onsubmit = function (e) {
//     e.preventDefault();

//     uploadfile();

//     document.getElementById('accountForm').submit();
// *****************************************************
