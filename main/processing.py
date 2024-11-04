import cv2
import numpy as np
import os

def getConrners(img, patternSize=(11,8), winSize=(5,5), zeroZone=(-1, -1), criteria=(cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 30, 0.001)): 
    grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 
    ret, corners = cv2.findChessboardCorners(grayimg, patternSize)
    corners = cv2.cornerSubPix(grayimg, corners, winSize, zeroZone, criteria)
    
    return ret, corners
def getCalibrationResult(database, folder):
    """
    This function is used to get the calibration result from the given folder.

    Args:
    database (object): The database object which contains some project information.
    folder (str): The path to the folder which contains the images.

    Returns:
        None
    """
    objpoint = np.zeros((11*8, 3), np.float32)
    objpoint[:,:2] = np.mgrid[0:11,0:8].T.reshape(-1,2)
    imgSize = (2048,2048)
    for img_name in os.listdir(folder):
        # prevent non-image files (e.g. folder)
        if not os.path.isfile(os.path.join(folder, img_name)):
            continue
        img_path = os.path.join(folder, img_name)
        img = cv2.imread(img_path)
        ret, corners = getConrners(img)
        database.corners.append(corners)
        database.objectPoints.append(objpoint)
        database.img_path.append(img_path)
    ret, ins, dist, rvec, tvec = cv2.calibrateCamera(database.objectPoints, imagePoints=database.corners, imageSize=imgSize, cameraMatrix=None, distCoeffs=None)
    database.rvec = rvec
    database.tvec = tvec
    database.distortion = dist
    database.intrinsic = ins
    
    return None