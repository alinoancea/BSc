function create_exp(form) {

    document.getElementById("button_exp").disabled = true;
    document.getElementById("status_exp").style.display = 'block';

    var myinterval;
    let args = {
        "vm_name": document.getElementById("vm_name").value,
        "vm_snapshot": document.getElementById("vm_snapshot").value,
        "vm_username": document.getElementById("vm_username").value,
        "vm_password": document.getElementById("vm_password").value,
        "malware_file": document.getElementById("malware_file").value
    }
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4) {
            if (this.status == 200) {
                console.log(this.responseText);
            } else {
                alert(this.responseText);
            }
        }
    };
    xhttp.open("POST", "/experiment/create");
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send(JSON.stringify(args));

    myinterval = setInterval(() => {
        let xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function() {
            if (this.readyState == 4) {
                if (this.status == 200) {
                    if (JSON.parse(this.responseText)['status'] != 'in progress') {
                        clearInterval(myinterval);
                        document.getElementById("button_exp").disabled = false;
                        document.getElementById("status_exp").style.display = 'none';

                        document.getElementById('exp_status_text').style.display = 'block';
                        document.getElementById('exp_status_text').innerText = JSON.parse(this.responseText)['status'];
                        setTimeout(() => {
                            document.getElementById('exp_status_text').style.display = 'none';
                        }, 5000);
                    }
                } else {
                    alert(this.responseText);
                }
            }
        };
        xhttp.open("GET", "/experiment/lastest");
        xhttp.send();
    }, 2000);
}