import cv2 as cv
import numpy as np

# Initiate
colors = [
    (255, 0, 0),   # Red
    (0, 255, 0),   # Green
    (0, 0, 255),   # Blue
    (255, 255, 0), # Cyan
    (255, 0, 255), # Magenta
    (0, 255, 255)  # Yellow
]
font = cv.FONT_HERSHEY_SIMPLEX
font_scale = 1
thickness = 2
line_type = cv.LINE_AA

def boxes_intersect(box1, box2):
    """Check if two boxes (x, y, w, h) intersect."""
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    if (x1 < x2 + w2 and x1 + w1 > x2 and
            y1 < y2 + h2 and y1 + h1 > y2):
        return True
    return False

def check_area(binary, min_area):
    check = False
    contours, _ = cv.findContours(binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    largest_contour = max(contours, key=cv.contourArea)
    area = cv.contourArea(largest_contour)
    if  area > min_area:
        check = True
    else: 
        check = False
    return check, area, largest_contour

def is_closed_circle(contour, circularity_threshold):
    check = False
    # Calculate area and perimeter
    area = cv.contourArea(contour)
    perimeter = cv.arcLength(contour, True)
    # Avoid division by zero
    if perimeter == 0:
        return False
    # Calculate circularity
    circularity = 4 * np.pi * (area / (perimeter ** 2))
    # Check if circularity is close to that of a circle
    if circularity > circularity_threshold:
        check = True
    else:
        check = False
    return check, circularity

def crop_circle(img, center, radius):
    # Create an empty mask with the same dimensions as the image
    mask = np.zeros_like(img)

    # Draw a filled circle in the mask where we want to keep the image
    cv.circle(mask, center, radius, (255), thickness=-1)
    # Apply the mask to the image
    cropped_image = cv.bitwise_and(img, img, mask=mask)
    return cropped_image

# Load the image
def countBlob(roi, min_blob, max_blob):
    check = False
    blobCount = 0
    contours, _ = cv.findContours(roi, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        # print(cv.contourArea(contour))
        if min_blob < cv.contourArea(contour) < max_blob:
            blobCount += 1
        if blobCount > 0:
            check = False
        else:
            check = True
    return check, blobCount

def check_cracks(roi, cx, cy, radius, cracks):
    check = False
    edged = cv.Canny(roi, 30, 150) 
    blur3 = cv.GaussianBlur(edged,(3,3),0)
    _, binary2 = cv.threshold(blur3, 70, 200, cv.THRESH_BINARY)
    crop_roi = crop_circle(binary2, (cx, cy), radius)
    white_pixels = np.sum(crop_roi == 200)
    if white_pixels < cracks: 
        check = True
    else: check = False
    return check, white_pixels

def matchCỉcle(img_path, template, threshold, top_left, bottom_right, segment):
    total_width = bottom_right[0] - top_left[0]
    segment_width = total_width // segment
    img = cv.imread(img_path)
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    assert img_gray is not None, "file could not be read, check with os.path.exists()"
    w, h = template.shape[::-1]
    for region_idx in range(segment):
        valid_boxes = []
        count = 0
        x_start = top_left[0] + region_idx * segment_width
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[2], 3)
        res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # Correct coordinates for original image
            new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
            if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            count +=1
            # color = colors[region_idx] # Use unique color for each region
            cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, count

def checkArea(img_path, template, threshold, top_left, bottom_right, segment, minArea):
    total_width = bottom_right[0] - top_left[0]
    segment_width = total_width // segment
    img = cv.imread(img_path)
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    assert img_gray is not None, "file could not be read, check with os.path.exists()"
    w, h = template.shape[::-1]
    for region_idx in range(segment):
        valid_boxes = []
        count = 0
        x_start = top_left[0] + region_idx * segment_width
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[2], 3)
        res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # Correct coordinates for original image
            new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
            if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            roi = sub_image[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            blur = cv.GaussianBlur(roi,(3,3),0)
            adjusted = cv.convertScaleAbs(blur, alpha=1.8, beta=50)
            _, binary = cv.threshold(adjusted, 210, 255, cv.THRESH_BINARY)
            check, area, _ = check_area(binary, minArea)
            
            if check:
                count +=1
                # color = colors[region_idx] # Use unique color for each region
                cv.putText(img, str(area), (x, y-5), font, font_scale, colors[1], thickness, line_type)
                cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, count

def checkCircle(img_path, template, threshold, top_left, bottom_right, segment, minArea, ecc):
    total_width = bottom_right[0] - top_left[0]
    segment_width = total_width // segment
    img = cv.imread(img_path)
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    assert img_gray is not None, "file could not be read, check with os.path.exists()"
    w, h = template.shape[::-1]
    for region_idx in range(segment):
        valid_boxes = []
        count = 0
        x_start = top_left[0] + region_idx * segment_width
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[2], 3)
        res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # Correct coordinates for original image
            new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
            if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            roi = sub_image[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            blur = cv.GaussianBlur(roi,(3,3),0)
            adjusted = cv.convertScaleAbs(blur, alpha=1.8, beta=50)
            _, binary = cv.threshold(adjusted, 210, 255, cv.THRESH_BINARY)
            check, _, contour= check_area(binary, minArea)
            if check:
                check, circularity = is_closed_circle(contour, ecc)
                if check:
                    count +=1
                    # color = colors[region_idx] # Use unique color for each region
                    cv.putText(img, str(round(circularity, 4)), (x, y-5), font, font_scale, colors[1], thickness, line_type)
                    cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, count


def checkStrange(img_path, template, threshold, top_left, bottom_right, segment, minArea, ecc, minBlob, maxBlob):
    total_width = bottom_right[0] - top_left[0]
    segment_width = total_width // segment
    img = cv.imread(img_path)
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    assert img_gray is not None, "file could not be read, check with os.path.exists()"
    w, h = template.shape[::-1]
    for region_idx in range(segment):
        valid_boxes = []
        count = 0
        x_start = top_left[0] + region_idx * segment_width
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[2], 3)
        res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # Correct coordinates for original image
            new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
            if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            roi = sub_image[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            blur = cv.GaussianBlur(roi,(3,3),0)
            adjusted = cv.convertScaleAbs(blur, alpha=1.8, beta=50)
            _, binary = cv.threshold(adjusted, 210, 255, cv.THRESH_BINARY)
            check, _, contour= check_area(binary, minArea)
            if check:
                check, _ = is_closed_circle(contour, ecc)
                if check:
                    M = cv.moments(contour)
                    if M['m00'] != 0:
                        cx = int(M['m10'] / M['m00'])  # x-coordinate of centroid
                        cy = int(M['m01'] / M['m00'])  # y-coordinate of centroid
                    else: cx = cy = 0
                    crop_roi = crop_circle(binary, (cx, cy), 48)
                    check, blobCount = countBlob(crop_roi, minBlob, maxBlob)
                    cv.putText(img, str(round(blobCount, 4)), (x, y-5), font, font_scale, colors[1], thickness, line_type)
                    if check:
                        count += 1
                        cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, count

def checkCracks(img_path, template, threshold, top_left, bottom_right, segment, minArea, ecc, minBlob, maxBlob, cracks):
    total_width = bottom_right[0] - top_left[0]
    segment_width = total_width // segment
    img = cv.imread(img_path)
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    assert img_gray is not None, "file could not be read, check with os.path.exists()"
    w, h = template.shape[::-1]
    for region_idx in range(segment):
        valid_boxes = []
        count = 0
        x_start = top_left[0] + region_idx * segment_width
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[2], 3)
        res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # Correct coordinates for original image
            new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
            if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            roi = sub_image[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            blur = cv.GaussianBlur(roi,(3,3),0)
            adjusted = cv.convertScaleAbs(blur, alpha=1.8, beta=50)
            _, binary = cv.threshold(adjusted, 210, 255, cv.THRESH_BINARY)
            check, _, contour= check_area(binary, minArea)
            if check:
                check, _ = is_closed_circle(contour, ecc)
                if check:
                    M = cv.moments(contour)
                    if M['m00'] != 0:
                        cx = int(M['m10'] / M['m00'])  # x-coordinate of centroid
                        cy = int(M['m01'] / M['m00'])  # y-coordinate of centroid
                    else: cx = cy = 0
                    crop_roi = crop_circle(binary, (cx, cy), 48)
                    check, _ = countBlob(crop_roi, minBlob, maxBlob)
                    if check:
                        check, white_pixels = check_cracks(blur, cx, cy, 33, cracks)
                        cv.putText(img, str(round(white_pixels, 4)), (x, y-5), font, font_scale, colors[1], thickness, line_type)
                        if check:
                            count += 1
                            cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, count

def final(img_path, template, threshold, top_left, bottom_right, segment, minArea, ecc, minBlob, maxBlob, cracks):
    total_width = bottom_right[0] - top_left[0]
    segment_width = total_width // segment
    img = cv.imread(img_path)
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    assert img_gray is not None, "file could not be read, check with os.path.exists()"
    w, h = template.shape[::-1]
    for region_idx in range(segment):
        valid_boxes = []
        count = 0
        x_start = top_left[0] + region_idx * segment_width
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[2], 3)
        res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # Correct coordinates for original image
            new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
            if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            roi = sub_image[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            blur = cv.GaussianBlur(roi,(3,3),0)
            adjusted = cv.convertScaleAbs(blur, alpha=1.8, beta=50)
            _, binary = cv.threshold(adjusted, 210, 255, cv.THRESH_BINARY)
            check, _, contour= check_area(binary, minArea)
            if check:
                check, _ = is_closed_circle(contour, ecc)
                if check:
                    M = cv.moments(contour)
                    if M['m00'] != 0:
                        cx = int(M['m10'] / M['m00'])  # x-coordinate of centroid
                        cy = int(M['m01'] / M['m00'])  # y-coordinate of centroid
                    else: cx = cy = 0
                    crop_roi = crop_circle(binary, (cx, cy), 48)
                    check, _ = countBlob(crop_roi, minBlob, maxBlob)
                    if check:
                        check, _ = check_cracks(blur, cx, cy, 33, cracks)
                        if check:
                            count += 1
                            cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, count