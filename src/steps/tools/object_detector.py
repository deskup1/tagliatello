from ultralytics import YOLO
import PIL.Image

# Load a pretrained YOLOv10n model
# model = YOLO("yolov10n.pt")

# # Perform object detection on an image
# results = model("image.jpg")

# # Display the results
# results[0].show()

class ObjectDetector:
    def __init__(self, model_name: str = "yolov8x.pt", treeshold = 0.4, objects_to_detect = ["person"], use_gpu = False):
        if use_gpu:
            import torch
            torch.cuda.set_device(0)
            self.model = YOLO(model_name, device="gpu")
        else:
            self.model = YOLO(model_name)
        self.treeshold = treeshold
        self.objects_to_detect = objects_to_detect

    def detect(self, image: PIL.Image.Image):
        results = self.model(image, save_txt = False)
        bounding_boxes = self._get_bounding_boxes(results)
        images = [self._get_image_from_bounding_box(image, bounding_box) for bounding_box in bounding_boxes]
        return images
    
    def _get_bounding_boxes(self, results):
        bounding_boxes = []
        confdence_scores = []
        for result in results:

            for i, cls in enumerate(result.boxes.cls):
                class_name = result.names[int(cls)]

                if class_name not in self.objects_to_detect:
                    continue

                confidence = result.boxes.conf[i].item()
                if confidence < self.treeshold:
                    continue

                x1, y1, x2, y2 = result.boxes.xyxy[i].tolist()

                bounding_boxes.append((x1, y1, x2, y2))
                confdence_scores.append(confidence)
                print(f"Found {class_name} with confidence {confidence}")

        # sort by confidence
        bounding_boxes = [bounding_box for _, bounding_box in sorted(zip(confdence_scores, bounding_boxes), reverse=True)]

        return bounding_boxes
    
    def _get_image_from_bounding_box(self, image, bounding_box):
        # bounding box in pixels
        x1, y1, x2, y2 = bounding_box
        # crop the image
        cropped_image = image.crop((x1, y1, x2, y2))
        return (cropped_image, bounding_box)
    

if __name__ == "__main__":
    image = PIL.Image.open("0142.png")
    detector = ObjectDetector()
    results = detector.detect(image)
    # Display the results
    for result in results:
        result[0].show()