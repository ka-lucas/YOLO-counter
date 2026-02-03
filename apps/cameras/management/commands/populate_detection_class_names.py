from django.core.management.base import BaseCommand
from apps.cameras.models import Camera


class Command(BaseCommand):
    help = 'Popula o campo detection_class_name para todas as câmeras'

    def handle(self, *args, **options):
        cameras = Camera.objects.all()
        updated_count = 0

        for camera in cameras:
            # O método save() já faz isso automaticamente
            # Mas forçar uma atualização para garantir
            class_dict = dict(Camera.YOLO_CLASSES)
            old_name = camera.detection_class_name
            camera.detection_class_name = class_dict.get(camera.detection_class, '')
            
            if old_name != camera.detection_class_name:
                camera.save(update_fields=['detection_class_name'])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ {camera.name}: {old_name or "(vazio)"} → {camera.detection_class_name}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n{updated_count} câmeras atualizadas com sucesso!')
        )
