from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings


class Camera(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cameras')
    name = models.CharField(max_length=100)

    rtsp_url = models.CharField(max_length=255, blank=True, null=True, help_text="URL RTSP (ex: rtsp://ip:port/path)")

    stream_url = models.URLField(blank=True, null=True, help_text="URL HTTP/MJPEG (ex: http://ip:port/mjpg/video.mjpg)")

    location = models.CharField(max_length=150, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Associação com modelo .pt
    model_config = models.ForeignKey(
        'configuracao.ModelConfiguration',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Modelo .pt associado à câmera"
    )
    
    # Classes YOLO disponíveis
    YOLO_CLASSES = [
        (0, 'person'),
        (1, 'bicycle'),
        (2, 'car'),
        (3, 'motorcycle'),
        (4, 'airplane'),
        (5, 'bus'),
        (6, 'train'),
        (7, 'truck'),
        (8, 'boat'),
        (9, 'traffic light'),
        (10, 'fire hydrant'),
        (11, 'stop sign'),
        (12, 'parking meter'),
        (13, 'bench'),
        (14, 'bird'),
        (15, 'cat'),
        (16, 'dog'),
        (17, 'horse'),
        (18, 'sheep'),
        (19, 'cow'),
        (20, 'elephant'),
        (21, 'bear'),
        (22, 'zebra'),
        (23, 'giraffe'),
        (24, 'backpack'),
        (25, 'umbrella'),
        (26, 'handbag'),
        (27, 'tie'),
        (28, 'suitcase'),
        (29, 'frisbee'),
        (30, 'skis'),
        (31, 'snowboard'),
        (32, 'sports ball'),
        (33, 'kite'),
        (34, 'baseball bat'),
        (35, 'baseball glove'),
        (36, 'skateboard'),
        (37, 'surfboard'),
        (38, 'tennis racket'),
        (39, 'bottle'),
        (40, 'wine glass'),
        (41, 'cup'),
        (42, 'fork'),
        (43, 'knife'),
        (44, 'spoon'),
        (45, 'bowl'),
        (46, 'banana'),
        (47, 'apple'),
        (48, 'sandwich'),
        (49, 'orange'),
        (50, 'broccoli'),
        (51, 'carrot'),
        (52, 'hot dog'),
        (53, 'pizza'),
        (54, 'donut'),
        (55, 'cake'),
        (56, 'chair'),
        (57, 'couch'),
        (58, 'potted plant'),
        (59, 'bed'),
        (60, 'dining table'),
        (61, 'toilet'),
        (62, 'tv'),
        (63, 'laptop'),
        (64, 'mouse'),
        (65, 'remote'),
        (66, 'keyboard'),
        (67, 'cell phone'),
        (68, 'microwave'),
        (69, 'oven'),
        (70, 'toaster'),
        (71, 'sink'),
        (72, 'refrigerator'),
        (73, 'book'),
        (74, 'clock'),
        (75, 'vase'),
        (76, 'scissors'),
        (77, 'teddy bear'),
        (78, 'hair drier'),
        (79, 'toothbrush'),
    ]
    
    # Classe YOLO para detecção (uma única classe por câmera)
    detection_class = models.IntegerField(
        choices=YOLO_CLASSES,
        default=0,
        help_text="Classe YOLO para detectar"
    )
    
    # Nome do label da classe (armazenado automaticamente)
    detection_class_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="Nome da classe YOLO selecionada"
    )

    class Meta:
        db_table = "cameras"

    def clean(self):
        if not self.rtsp_url and not self.stream_url:
            raise ValidationError("Informe pelo menos uma URL (RTSP ou HTTP).")
        
        # Validar formato RTSP
        if self.rtsp_url and not self.rtsp_url.startswith('rtsp://'):
            raise ValidationError("URL RTSP deve começar com 'rtsp://'")
        
        # Validar formato HTTP para MJPEG
        if self.stream_url and not (self.stream_url.startswith('http://') or self.stream_url.startswith('https://')):
            raise ValidationError("URL de stream deve começar com 'http://' ou 'https://'")

    @property
    def primary_url(self):
        """Retorna a URL primária para uso (prioriza HTTP/MJPEG)"""
        return self.stream_url or self.rtsp_url
    
    @property
    def stream_type(self):
        """Retorna o tipo de stream"""
        if self.stream_url:
            return 'HTTP/MJPEG'
        elif self.rtsp_url:
            return 'RTSP'
        return 'Não configurado'

    def save(self, *args, **kwargs):
        # Automaticamente salva o nome da classe baseado no ID
        if self.detection_class is not None:
            class_dict = dict(self.YOLO_CLASSES)
            self.detection_class_name = class_dict.get(self.detection_class, '')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name