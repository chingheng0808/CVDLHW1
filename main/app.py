from flask import Flask, g, render_template, jsonify, request, send_from_directory, send_file
import os
import cv2
import numpy as np
from processing import getConrners, getCalibrationResult
import shutil

app = Flask(__name__)

UPLOAD_IMG1 = 'upload_img1'
UPLOAD_IMG2 = 'upload_img2'
UPLOAD_IMGL = 'upload_imgL'
UPLOAD_IMGR = 'upload_imgR'
UPLOAD_FOLDER = 'upload_folder'
app.config['UPLOAD_IMG1'] = UPLOAD_IMG1
app.config['UPLOAD_IMG2'] = UPLOAD_IMG2
app.config['UPLOAD_IMGL'] = UPLOAD_IMGL
app.config['UPLOAD_IMGR'] = UPLOAD_IMGR
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DISPLACEMENT = [[7,5], [4,5], [1,5], [7,2], [4,2], [1,2]] # for board showing position translation
DELDICT = {
    '1': ['upload_folder/onboard', 'upload_folder/vertical', 'upload_folder/Q2_Image','stereo', 'keypoints', 'match_keypoints', 'upload_img1', 'upload_img2', 'upload_imgL', 'upload_imgR'],
    '2': ['upload_folder/corners', 'upload_folder/undistorted', 'upload_folder/Q1_Image','stereo', 'keypoints', 'match_keypoints', 'upload_img1', 'upload_img2', 'upload_imgL', 'upload_imgR'],
    '3': ['upload_folder/corners', 'upload_folder/undistorted', 'upload_folder/Q1_Image', 'upload_folder/onboard', 'upload_folder/vertical', 'upload_folder/Q2_Image', 'keypoints', 'match_keypoints', 'upload_img1', 'upload_img2'],
    '4': ['upload_folder/corners', 'upload_folder/undistorted', 'upload_folder/Q1_Image', 'upload_folder/onboard', 'upload_folder/vertical', 'upload_folder/Q2_Image', 'stereo', 'upload_imgL', 'upload_imgR'],
}
class Database:
    def __init__(self):
        self.currentFolder = ''
        self.clearStatus()
    def clearStatus(self):
        self.corners = []
        self.objectPoints = []
        self.img_path = []
        self.rvec = None
        self.tvec = None
        self.intrinsic = None
        self.distortion = None
        self.img_type = None

database = Database()

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/home/upload_image', methods=['POST'])
def loadImage():
    database.clearStatus()
    if 'image' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    
    file = request.files['image']
    img_type = request.form.get('img_type')
    print(img_type)
    
    database.img_type = img_type
    
    # 檢查文件是否有效
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    os.makedirs(app.config[f'UPLOAD_IMG{img_type}'], exist_ok=True)
    # 保存文件
    file_path = os.path.join(app.config[f'UPLOAD_IMG{img_type}'], file.filename)
    if len(os.listdir(app.config[f'UPLOAD_IMG{img_type}'])) > 0:
        os.remove(os.path.join(app.config[f'UPLOAD_IMG{img_type}'], os.listdir(app.config[f'UPLOAD_IMG{img_type}'])[0]))
    file.save(file_path)
    image_url = file_path
    
    return jsonify({"message": f"Image uploaded successfully as {file.filename}", "image_url": image_url}), 200

@app.route('/<img_folder>/<filename>')
def uploaded_fileL(img_folder, filename):
    file_path = os.path.join(img_folder, filename)
    # 使用 send_file 返回文件
    return send_file(file_path)
@app.route('/get_single_image/<img_type>', methods=['GET'])
def get_single_image(img_type):
    images = [f'/{app.config[f"UPLOAD_IMG{img_type}"]}/{f}' for f in os.listdir(app.config[f'UPLOAD_IMG{img_type}']) if f.endswith(('jpg','png','jpeg','bmp'))]
    return jsonify({"image": images[0]}), 200

################### LOAD FOLDER ###################
@app.route('/home/upload_folder', methods=['POST'])
def loadFolder():
    files = request.files.getlist('files[]')
    paths = request.form.getlist('paths[]')  # 獲取相對路徑

    if not files:
        return jsonify({"message": "No files uploaded"}), 400

    # 設置 currentFolder
    if paths:
        database.currentFolder = paths[0].split('/')[0]

    # 保存所有上傳的文件
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    for file, relative_path in zip(files, paths):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], relative_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)

    return jsonify({"message": "Folder uploaded successfully"}), 200

# 動態設置文件下載路徑
@app.route('/uploaded_folder/<path:filename>')
def uploaded_folder(filename):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], database.currentFolder)
    return send_from_directory(folder_path, filename)

# 獲取圖片列表
@app.route('/get_org_images')
def get_org_images():
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], database.currentFolder)
    images = [f'/uploaded_folder/{f}' for f in os.listdir(folder_path) if f.endswith('.bmp')]
    return jsonify({"images": images}), 200
####################### 1.1 FIND CORNERS ###################
@app.route('/home/1.1')
def findCorners():
    deleteFolders(DELDICT['1'])
    folder = os.path.join(app.config['UPLOAD_FOLDER'], database.currentFolder)
    
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'corners'), exist_ok=True)
    objpoint = np.zeros((11*8, 3), np.float32)
    objpoint[:,:2] = np.mgrid[0:11,0:8].T.reshape(-1,2)
    # print(objpoint.shape)。
    database.clearStatus()
    ## Parameters
    w, h = 11, 8
    winSize = (5,5)
    zeroZone = (-1, -1)
    criteria = (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 30, 0.001)
    for img_name in os.listdir(folder):
        database.img_path.append(img_name)
        img_path = os.path.join(folder, img_name)
        img = cv2.imread(img_path)
        
        ret, corners = getConrners(img, patternSize=(w,h), winSize=winSize, zeroZone=zeroZone, criteria=criteria)
        database.corners.append(corners)
        database.objectPoints.append(objpoint)
        # print(corners.shape) # 88*1*2
        # plot corners on image
        output = cv2.drawChessboardCorners(img, (w, h), corners, ret)
        cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], 'corners',f'{img_name}_corners.bmp'), output)
        
    return jsonify({"message": "Corners images saved successfully"}), 200
@app.route('/upload_folder/corners/<filename>')
def uploaded_cornered(filename):
    corner_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'corners')
    return send_from_directory(corner_folder, filename)
@app.route('/get_corner_images')
def get_corner_images():
    corner_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'corners')
    images = [os.path.join(corner_folder, f) for f in os.listdir(corner_folder) if f.endswith('_corners.bmp')]
    return jsonify({"images": images}), 200
####################### 1.2 FIND INTRINSICS ###################
@app.route('/home/1.2')
def findIntrinsics():
    deleteFolders(DELDICT['1'])
    imageSize = (2048,2048)
    ret, ins, dist, rvec, tvec=cv2.calibrateCamera(database.objectPoints, imagePoints=database.corners, imageSize=imageSize, cameraMatrix=None, distCoeffs=None)
    database.rvec = rvec
    database.tvec = tvec
    database.distortion = dist
    database.intrinsic = ins
    print(ins)
    # ins = json.dumps(ins.tolist(), ) # convert np array to string for parsing to json
    return jsonify({"message": "Finding intrinsics successfully", "ins": ins.tolist()}), 200
####################### 1.3 FIND EXTRINSICS ###################
@app.route('/home/1.3', methods=['POST'])
def findExtrinsics():
    deleteFolders(DELDICT['1'])
    data = request.get_json()
    selectImgID = int(data.get("number")) - 1 
    
    rotation_matrix = cv2.Rodrigues(database.rvec[selectImgID])[0]
    extrinsic_matrix = np.hstack((rotation_matrix , database.tvec[selectImgID]))
    
    print(f'{database.img_path[selectImgID]}: \n{extrinsic_matrix}')

    return jsonify({"message": "Finding extrinsics successfully", 'img_name': database.img_path[selectImgID], 'exts': extrinsic_matrix.tolist()}), 200
####################### 1.4 FIND DISTORTION ###################
@app.route('/home/1.4')
def findDistortion():
    deleteFolders(DELDICT['1'])
    print(database.distortion)
    return jsonify({"message": "Finding distortion successfully", 'distortion': database.distortion.tolist()}), 200
@app.route('/home/1.5')
def showUndistorted():
    deleteFolders(DELDICT['1'])
    folder = os.path.join(app.config['UPLOAD_FOLDER'], database.currentFolder)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'undistorted'), exist_ok=True)
    for img_name in os.listdir(folder):
        img_path = os.path.join(folder, img_name)
        img = cv2.imread(img_path)
        grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        undistorted_img = cv2.undistort(grayimg, database.intrinsic, database.distortion)
        cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], 'undistorted',f'{img_name}_undistorted.bmp'), undistorted_img)
    return jsonify({"message": "Show undistorted image successfully"}), 200
@app.route('/upload_folder/undistorted/<filename>')
def uploaded_undistorted(filename):
    distorted_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'undistorted')
    return send_from_directory(distorted_folder, filename)
@app.route('/get_undistorted_images')
def get_undistorted_images():
    distorted_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'undistorted')
    images = [os.path.join(distorted_folder, f) for f in os.listdir(distorted_folder) if f.endswith('_undistorted.bmp')]
    return jsonify({"images": images}), 200
####################### 2.1 Show Words on Board ###################
@app.route('/home/2.1', methods=['POST'])
def drawWordsonBoard():
    deleteFolders(DELDICT['2'])
    drawWords(database, mode='onboard')
    return jsonify({"message": "Show words on board successfully"}), 200
@app.route('/upload_folder/onboard/<filename>')
def uploaded_word_images_onboard(filename):
    onboard_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'onboard')
    return send_from_directory(onboard_folder, filename)
@app.route('/get_word_images_onboard')
def get_word_images_onboard():
    onboard_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'onboard')
    images = [os.path.join(onboard_folder, f) for f in os.listdir(onboard_folder) if f.endswith('onboard.bmp')]
    return jsonify({"images": images}), 200

####################### 2.2 Show Words Vertically ###################
@app.route('/home/2.2', methods=['POST'])
def drawWordsVertically():
    deleteFolders(DELDICT['2'])
    drawWords(database, mode='vertical')
    return jsonify({"message": "Show words vertically successfully"}), 200

@app.route('/upload_folder/vertical/<filename>')
def uploaded_word_images_vertical(filename):
    vertical_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'vertical')
    return send_from_directory(vertical_folder, filename)
@app.route('/get_word_images_vertical')
def get_word_images_vertical():
    vertical_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'vertical')
    images = [os.path.join(vertical_folder, f) for f in os.listdir(vertical_folder) if f.endswith('vertical.bmp')]
    return jsonify({"images": images}), 200
####################### 3.1 Stereo Disparity Map ###################
@app.route('/home/3.1')
def stereoDisparityMap():
    deleteFolders(DELDICT['3'])
    img_L_path = os.path.join(app.config['UPLOAD_IMGL'], os.listdir(app.config['UPLOAD_IMGL'])[0])
    img_R_path = os.path.join(app.config['UPLOAD_IMGR'], os.listdir(app.config['UPLOAD_IMGR'])[0])
    img_L = cv2.imread(img_L_path, cv2.CV_8U)
    img_R = cv2.imread(img_R_path, cv2.CV_8U)
    os.makedirs('stereo', exist_ok=True)
    stereo = cv2.StereoBM_create(numDisparities=432, blockSize=25)
    disparity = stereo.compute(img_L, img_R)
    disparity = cv2.normalize(disparity, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    cv2.imwrite(os.path.join('stereo', f'stereo_disparity.{img_L_path.split(".")[-1]}'), disparity)
    return jsonify({"message": "Stereo disparity map successfully"}), 200
@app.route('/stereo/<filename>')
def uploaded_stereo_disparity_map(filename):
    return send_from_directory('stereo', filename)
@app.route('/get_stereo_disparity_map')
def get_stereo_disparity_map():
    image_url = os.listdir('stereo')[0]
    image_url = os.path.join('stereo', image_url)
    return jsonify({"map": image_url}), 200
####################### 4.3 Keypoints ###################
@app.route('/home/4.3')
def getKeypoints():
    deleteFolders(DELDICT['4'])
    img_path = os.path.join(app.config['UPLOAD_IMG1'], os.listdir(app.config['UPLOAD_IMG1'])[0])
    gray = cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2GRAY)
    sift = cv2.SIFT_create()
    keypoints, descriptors = sift.detectAndCompute(gray, None)
    img = cv2.drawKeypoints(gray, keypoints, None, color=(0,255,0))
    os.makedirs('keypoints', exist_ok=True)
    cv2.imwrite(os.path.join('keypoints', f'{os.path.basename(img_path).split(".")[0]}_keypoints.{img_path.split(".")[-1]}'), img)
    
    return jsonify({"message": "Get keypoints successfully"}), 200
@app.route('/keypoints/<filename>')
def uploaded_keypoints(filename):
    return send_from_directory('keypoints', filename)
@app.route('/get_keypoints')
def get_keypoints():
    image_url = os.listdir('keypoints')[0]
    image_url = os.path.join('keypoints', image_url)
    return jsonify({"keypoints": image_url}), 200
####################### 4.4 Match Keypoints ###################
@app.route('/home/4.4')
def getMatchKeypoints():
    deleteFolders(DELDICT['4'])
    img1_path = os.path.join(app.config['UPLOAD_IMG1'], os.listdir(app.config['UPLOAD_IMG1'])[0])
    img2_path = os.path.join(app.config['UPLOAD_IMG2'], os.listdir(app.config['UPLOAD_IMG2'])[0])
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    os.makedirs('match_keypoints', exist_ok=True)
    sift = cv2.SIFT_create()
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append([m])
    matched_img = cv2.drawMatchesKnn(gray1, kp1, gray2, kp2, good_matches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    cv2.imwrite(os.path.join('match_keypoints', f'{os.path.basename(img1_path).split(".")[0]}_match_keypoints.{img1_path.split(".")[-1]}'), matched_img)
    return jsonify({"message": "Get match keypoints successfully"}), 200
@app.route('/match_keypoints/<filename>')
def uploaded_match_keypoints(filename):
    return send_from_directory('match_keypoints', filename)
@app.route('/get_match_keypoints')
def get_match_keypoints():
    image_url = os.listdir('match_keypoints')[0]
    image_url = os.path.join('match_keypoints', image_url)
    return jsonify({"match_keypoints": image_url}), 200

####################################################################
def drawWords(database, mode='onboard'):
    database.clearStatus()
    data = request.get_json()
    input_text = data.get("text")
    
    folder = os.path.join(app.config['UPLOAD_FOLDER'], database.currentFolder)
    ### Find corners and calibrate camera ###
    getCalibrationResult(database, folder)
    
    ### Read alphabet data ###
    ## note: the 'alphabet_db_onboard.txt' must be in the only folder which is in input folder.
    sub_fls = [fl for fl in os.listdir(folder) if os.path.isdir(os.path.join(folder,fl))]
    fs = cv2.FileStorage(os.path.join(folder, sub_fls[0], f'alphabet_db_{mode}.txt'), cv2.FILE_STORAGE_READ)
    cp_raw_list = [] # len = number of characters
    for idx, char in enumerate(input_text):
        charpoints = fs.getNode(char).mat()
        for line in charpoints:
            line[0][0] += DISPLACEMENT[idx][0]
            line[1][0] += DISPLACEMENT[idx][0]
            line[0][1] += DISPLACEMENT[idx][1]
            line[1][1] += DISPLACEMENT[idx][1]
        cp_raw_list.append(charpoints) 

    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], mode), exist_ok=True)
    ### Draw words on board ###
    for idx, img_path in enumerate(database.img_path):
        cp_trans_list = []
        # get projected points coordinates
        for charPoints in cp_raw_list:
            trans_points, _ = cv2.projectPoints(np.array(charPoints, np.float32).reshape(-1,3), database.rvec[idx], database.tvec[idx], database.intrinsic, database.distortion)
            cp_trans_list.append(trans_points)
        img = cv2.imread(img_path)
        for cp in cp_trans_list:
            # print(len(cp))
            for i in range(0, len(cp), 2): ## sequentially, every 2 points corresponds to a line
                
                pointA = (int(cp[i][0][0]), int(cp[i][0][1])) 
                pointB = (int(cp[i + 1][0][0]), int(cp[i + 1][0][1])) 
                # print(pointA, pointB)
                img = cv2.line(img, pointA, pointB, color=(0, 0, 255), thickness=5)
        img_name = os.path.basename(img_path)
        cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], mode, f'{img_name}_{mode}.bmp'), img)
def deleteFolders(del_list):
    for fl in del_list:
        shutil.rmtree(fl, ignore_errors=True)
if __name__ == '__main__':
    app.run(debug=True)
