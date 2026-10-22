from ultralytics import YOLO
import cv2

model = YOLO("yolo11n.pt")

cap = cv2.VideoCapture("traffic.mp4")

while True:
    ret,frame = cap.read()
    
    if not ret:
        break
    
    results = model(frame)
    
    vehicle_count = 0
    
    for result in results:
        for box in result.boxes:
            
            cls = int(box.cls[0])
            
            if cls in [2,3,5,7]:
                vehicle_count += 1
                
    annotated_frame = results[0].plot()
    
    cv2.putText(
        annotated_frame,
        f"Vehicles: {vehicle_count}",
        (20,40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0,255,0),
        2
    )
    if vehicle_count > 15:
        cv2.putText(
            annotated_frame,
            f"Congested",
            (20,70),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0,0,255),
            2
        )
    
    cv2.imshow("Traffic Detection", annotated_frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
cv2.release()
cv2.destroyAllWindows()
    