// GLOBAL VARIABLES //
let intervalId = null;
let isAR = false;

document.addEventListener("DOMContentLoaded", function () {
        document.getElementById("btnLoadFolder").addEventListener("click", function () {
                document.getElementById("folder_input").click();
        });
        document.getElementById("folder_input").addEventListener("change", function(event) {
                const files = event.target.files;
                const formData = new FormData();
                // 將所有選定的文件加入到 formData 中，並保留相對路徑
                for (let i = 0; i < files.length; i++) {
                        formData.append("files[]", files[i]);
                        formData.append("paths[]", files[i].webkitRelativePath);  // 使用相對路徑
                }
                // 將文件列表發送到 Flask 後端
                fetch('/home/upload_folder', {
                        method: 'POST',
                        body: formData
                })
                .then(response => response.json())
                .then(data => console.log(data.message))
                .catch(error => console.error('Error:', error));
        });
        document.getElementById("btnLoadImgL").addEventListener("click", function () {
                document.getElementById("input_L").click();
        });
        document.getElementById("btnLoadImgR").addEventListener("click", function () {
                document.getElementById("input_R").click();
        });
        document.getElementById("btnLoadImg1").addEventListener("click", function () {
                document.getElementById("input_1").click();
        });
        document.getElementById("btnLoadImg2").addEventListener("click", function () {
                document.getElementById("input_2").click();
        });
        document.getElementById("input_L").addEventListener("change", async function() {
                const file = this.files[0];
                await loadAnInage(file, "L");

                fetch('/get_single_image/L')
                .then(response => response.json())
                .then(data => {displaySingleImage(data.image, 'Left Image', 1)})
                .catch(error => console.error('Error:', error));
        });
        document.getElementById("input_R").addEventListener("change", async function() {
                const file = this.files[0];
                await loadAnInage(file, "R");

                fetch('/get_single_image/R')
                .then(response => response.json())
                .then(data => displaySingleImage(data.image, 'Right Image', 2))
                .catch(error => console.error('Error:', error));
        });
        document.getElementById("input_1").addEventListener("change", async function() {
                const file = this.files[0];
                await loadAnInage(file, "1");

                fetch('/get_single_image/1')
                .then(response => response.json())
                .then(data => displaySingleImage(data.image, 'Image 1', 1))
                .catch(error => console.error('Error:', error));
        });
        document.getElementById("input_2").addEventListener("change", async function() {
                const file = this.files[0];
                await loadAnInage(file, "2");

                fetch('/get_single_image/2')
                .then(response => response.json())
                .then(data => displaySingleImage(data.image, 'Image 2', 2))
                .catch(error => console.error('Error:', error));
        });
        document.getElementById("btnFindCorners").addEventListener("click", function () {
                isAR = false;
                findCorners(); /** /home/1.1 **/ 
        })
        document.getElementById("btnIntrinsics").addEventListener("click", function () {
                fetch('/home/1.2')
                .then(response => response.json())
                .then(data => {
                        isAR = false;
                        let ins = data.ins;
                        // ins = JSON.parse(ins); // Convert string to Array
                        console.log(ins);
                })
                .catch(error => console.error('Error:', error));
        })
        document.getElementById("btnExtrinsics").addEventListener("click", function () {
                const selectImgID = document.getElementById("selectImgID").value;
                console.log(selectImgID);
                
                fetch('/home/1.3', {
                        method: 'POST',
                        headers: {
                                'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ number: selectImgID })  // 將選定的數字包裝為 JSON 格式
                })
                .then(response => response.json())
                .then(data => {
                        isAR = false;
                        let exts = data.exts;
                        let img_name = data.img_name;
                        console.log(img_name,exts); 
                })
                .catch(error => console.error('Error:', error));
        })
        document.getElementById("btnDistortion").addEventListener("click", function () {
                fetch('/home/1.4')
                .then(response => response.json())
                .then(data => {
                        isAR = false;
                        let dist = data.distortion;
                        console.log(dist);
                })
                .catch(error => console.error('Error:', error));
        })
        document.getElementById("btnCalibResult").addEventListener("click", function () {
                fetch('/home/1.5')
                .then(response => response.json())
                .catch(error => console.error('Error:', error));
                hideImgBlocks();
                Promise.all([
                        fetch('/get_undistorted_images').then(response => response.json()),
                        fetch('/get_org_images').then(response => response.json())
                ])
                .then(([result1, result2]) => {
                        isAR = false;
                        // 當兩個請求都完成後進行處理
                        if(intervalId != null){
                                clearInterval(intervalId); // clear interval used in findCorners
                                intervalId = null;
                        }
                        
                        undist_imgs = result1.images;
                        org_imgs = result2.images;
                        
                        let index = 0;
                        const imgElement1 = document.getElementById(`imageDisplay1`);
                        const imgElement2 = document.getElementById(`imageDisplay2`);
                        const textElement1 = document.getElementById(`img1text`);
                        const textElement2 = document.getElementById(`img2text`);
                        imgElement1.style.display = "block";
                        imgElement2.style.display = "block";
                        textElement1.style.display = "block";
                        textElement2.style.display = "block";

                        textElement1.textContent = 'Distorted Image';
                        textElement2.textContent = 'Undistorted Image';

                        intervalId = setInterval(() => {
                                if(index >= undist_imgs.length){
                                        clearInterval(intervalId);
                                        intervalId = null;
                                        return
                                }
                                imgElement1.src = org_imgs[index];
                                imgElement2.src = undist_imgs[index];
                                index = index + 1; 
                        }, 1000);
                })
                .catch(error => {
                console.error('Error:', error);
                });
        })
        document.getElementById("btnARonBoard").addEventListener("click", async function () {
                const inputText = document.getElementById("inputText").value;
                if (inputText == "") {
                        alert("Please enter a text.");
                        return;
                }
                else if (inputText.length > 6) {
                        alert("Text length should be less than 6.");
                        return;
                }
                console.log(inputText);
                document.getElementById("imageDisplay3").style.display = "none";
                document.getElementById("img3text").style.display = "none";
                
                // POST Request to backend
                const response = await fetch('/home/2.1', {
                        method: 'POST',
                        headers: {
                                'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({text: inputText})  
                })
                if(!response.ok){
                        alert("Error: " + "Is there no db in the input folder?");
                        return;
                }
                const result = await response.json();
                console.log(result.message);

                // Get word images and show
                fetch('/get_word_images_onboard')
                .then(response => response.json())
                .then(data => {
                        isAR = true;
                        displaySingleStream(data.images, `onBoard Word Image: ${document.getElementById("inputText").value}`, 1); // onboard always display on 1
                }).catch(error => console.error('Error:', error));
        })
        document.getElementById("btnARVertical").addEventListener("click", async function () {
                const inputText = document.getElementById("inputText").value;
                if (inputText == "") {
                        alert("Please enter a text.");
                        return;
                }
                else if (inputText.length > 6) {
                        alert("Text length should be less than 6.");
                        return;
                }
                console.log(inputText);
                document.getElementById("imageDisplay3").style.display = "none";
                document.getElementById("img3text").style.display = "none";
                
                // POST Request to backend
                const response = await fetch('/home/2.2', {
                        method: 'POST',
                        headers: {
                                'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({text: inputText})  
                })
                const result = await response.json();
                console.log(result.message);

                // Get word images and show
                fetch('/get_word_images_vertical')
                .then(response => response.json())
                .then(data => {
                        isAR = true;
                        displaySingleStream(data.images, `Vertical Word Image: ${document.getElementById("inputText").value}`, 2); // vertical always display on 2
                }).catch(error => console.error('Error:', error));
        })
        document.getElementById("btnGenerateMap").addEventListener("click", async function () {
                try {
                        // 發送第一個請求
                        const response1 = await fetch('/home/3.1');
                        if (!response1.ok) {
                                throw new Error(`Failed to fetch /home/3.1: ${response1.statusText}`);
                        }
                        const data1 = await response1.json();
                        console.log(data1.message);
                
                        // 發送第二個請求，在第一個請求完成後
                        const response2 = await fetch('/get_stereo_disparity_map');
                        if (!response2.ok) {
                                throw new Error(`Failed to fetch /get_stereo_disparity_map: ${response2.statusText}`);
                        }
                        const data2 = await response2.json();
                        displaySingleImage(data2.map, 'Disparity Map', 3);
        
                } catch (error) {
                        console.error('Error:', error);
                }
        })
        document.getElementById('btnKeypoints').addEventListener('click', async function() {
                try{
                        const response1 = await fetch('/home/4.3');
                        const result1 = await response1.json();
                        console.log(result1.message);
                        
                        const response2 = await fetch('/get_keypoints')
                        const data = await response2.json();
                        displaySingleImage(data.keypoints, 'Keypoints', 2);
                }catch (error) {
                        console.error('Error:', error);
                }
        })
        document.getElementById('btnMatched').addEventListener('click', async function() {
                try{
                        const response1 = await fetch('/home/4.4');
                        const result1 = await response1.json();
                        console.log(result1.message);
                        
                        const response2 = await fetch('/get_match_keypoints')
                        const data = await response2.json();
                        displaySingleImage(data.match_keypoints, 'Matched Keypoints', 3);
                }catch (error) {
                        console.error('Error:', error);
                }
        })
        document.getElementById('btnClearImage').addEventListener('click', function() {
                hideImgBlocks(true);
        })
});

async function loadAnInage(file, img_type) {
        if (!file) {
                alert("Please select an image to upload.");
                return;
        }

        console.log("Selected file: " + file.name);

        // 使用 FormData 將文件封裝
        const formData = new FormData();
        formData.append("image", file);
        formData.append("img_type", img_type);  // image type (1/2/L/R)

        try {
        const response = await fetch('/home/upload_image', {
                method: 'POST',
                body: formData
        });

        if (!response.ok) {
                throw new Error(`Failed to upload image: ${response.statusText}`);
        }

        const data = await response.json();
        console.log("Server response:", data);
        if (data.message) {
                alert(data.message);  // 根據後端返回的消息顯示提示
        }

        } catch (error) {
                console.error('Error:', error);
        }
}
async function findCorners() {
        // 調用後端的角點檢測函數
        const response = await fetch('/home/1.1');
        const result = await response.json();
        console.log(result.message);

        // 從後端獲取角點圖片列表
        fetch('/get_corner_images')
        .then(response => response.json())
        .then(data => {
                displaySingleStream(data.images, 'Corners', 1);
        })
        .catch(error => console.error('Error:', error));
}
function displaySingleImage(image, text, disId=2) {
        const imgElement = document.getElementById(`imageDisplay${disId}`);
        imgElement.src = "";

        document.getElementById(`img${disId}text`).textContent = text;
        document.getElementById(`img${disId}text`).style.display = "block";
        document.getElementById(`imageDisplay${disId}`).style.display = "block";
        
        if(intervalId != null){
                clearInterval(intervalId); // clear interval if intervalId exists
                intervalId = null;
        }
        console.log(image);
        imgElement.src = image;
}
function displaySingleStream(images, text, disId=2) {
        if(!isAR){hideImgBlocks();}
        let index = 0;
        const imgElement = document.getElementById(`imageDisplay${disId}`);

        document.getElementById(`img${disId}text`).textContent = text;
        document.getElementById(`img${disId}text`).style.display = "block";
        document.getElementById(`imageDisplay${disId}`).style.display = "block";
        
        if(intervalId != null){
                clearInterval(intervalId); // clear interval if intervalId exists
                intervalId = null;
        }
        
        intervalId = setInterval(() => {
                if(index >= images.length){
                        clearInterval(intervalId);
                        intervalId = null;
                        return
                }
                imgElement.src = images[index];
                index = index + 1; 
        }, 1000); // 每秒顯示一張圖片
}
function hideImgBlocks(clear=false) {
        if(clear){
                document.getElementById("imageDisplay1").src = "";
                document.getElementById("imageDisplay2").src = "";
                document.getElementById("imageDisplay3").src = "";
                document.getElementById("img1text").textContent = "";
                document.getElementById("img2text").textContent = "";
                document.getElementById("img3text").textContent = "";
        }
        document.getElementById("imageDisplay1").style.display = "none";
        document.getElementById("imageDisplay2").style.display = "none";
        document.getElementById("imageDisplay3").style.display = "none";
        document.getElementById("img1text").style.display = "none";
        document.getElementById("img2text").style.display = "none";
        document.getElementById("img3text").style.display = "none";
        return
}