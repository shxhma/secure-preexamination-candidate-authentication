import os
import cv2
import math
import torch
import numpy as np
import torch.nn.functional as F
from collections import OrderedDict
from src.model_lib.MiniFASNet import MiniFASNetV1, MiniFASNetV2, MiniFASNetV1SE, MiniFASNetV2SE
from src.data_io import transform as trans
from src.utility import get_kernel, parse_model_name

MODEL_MAPPING = {
    'MiniFASNetV1':   MiniFASNetV1,
    'MiniFASNetV2':   MiniFASNetV2,
    'MiniFASNetV1SE': MiniFASNetV1SE,
    'MiniFASNetV2SE': MiniFASNetV2SE
}

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Detection:
    def __init__(self):
        caffemodel = os.path.join(_BASE_DIR, "resources", "detection_model", "Widerface-RetinaFace.caffemodel")
        deploy     = os.path.join(_BASE_DIR, "resources", "detection_model", "deploy.prototxt")
        self.detector            = cv2.dnn.readNetFromCaffe(deploy, caffemodel)
        self.detector_confidence = 0.6

    def get_bbox(self, img):
        height, width = img.shape[0], img.shape[1]
        aspect_ratio  = width / height
        if img.shape[1] * img.shape[0] >= 192 * 192:
            img = cv2.resize(img,
                             (int(192 * math.sqrt(aspect_ratio)),
                              int(192 / math.sqrt(aspect_ratio))),
                             interpolation=cv2.INTER_LINEAR)
        blob = cv2.dnn.blobFromImage(img, 1, mean=(104, 117, 123))
        self.detector.setInput(blob, 'data')
        out           = self.detector.forward('detection_out').squeeze()
        max_conf_index = np.argmax(out[:, 2])
        left, top, right, bottom = (
            out[max_conf_index, 3] * width,
            out[max_conf_index, 4] * height,
            out[max_conf_index, 5] * width,
            out[max_conf_index, 6] * height,
        )
        return [int(left), int(top), int(right - left + 1), int(bottom - top + 1)]

class AntiSpoofPredict(Detection):
    def __init__(self, device_id):
        super(AntiSpoofPredict, self).__init__()
        self.device       = torch.device(
            "cuda:{}".format(device_id) if torch.cuda.is_available() else "cpu"
        )
        self._model_cache = {}   # ← cache: path → model (load once, reuse forever)

    def _load_model(self, model_path):
        if model_path in self._model_cache:
            return self._model_cache[model_path]

        model_name  = os.path.basename(model_path)
        h_input, w_input, model_type, _ = parse_model_name(model_name)
        kernel_size = get_kernel(h_input, w_input)
        model       = MODEL_MAPPING[model_type](conv6_kernel=kernel_size).to(self.device)

        state_dict      = torch.load(model_path, map_location=self.device)
        first_layer_name = next(iter(state_dict))
        if first_layer_name.startswith('module.'):
            new_state_dict = OrderedDict(
                (k[7:], v) for k, v in state_dict.items()
            )
            model.load_state_dict(new_state_dict)
        else:
            model.load_state_dict(state_dict)

        model.eval()   # set once here — no need to call every predict

        self._model_cache[model_path] = model
        print(f"  Loaded model: {model_name}")
        return model

    def predict(self, img, model_path):
        test_transform = trans.Compose([trans.ToTensor()])
        img   = test_transform(img).unsqueeze(0).to(self.device)
        model = self._load_model(model_path)   # fast — uses cache after first call

        with torch.no_grad():
            result = model.forward(img)
            result = F.softmax(result, dim=1).cpu().numpy()   # dim=1 fix
        return result