from picamera2 import Picamera2
from datetime import datetime
import time
import numpy as np
from PIL import Image, ImageFilter, ImageOps
import os

class CameraController:
    def __init__(self):
        self.camera = Picamera2()
        self.effects = {
            'normal': self._apply_normal,
            'negative': self._apply_negative,
            'sketch': self._apply_sketch,
            'colorswap': self._apply_colorswap
        }
        
        os.makedirs('photos', exist_ok=True)
        
    def _apply_normal(self, image):
        """No effect applied"""
        return image
    
    def _apply_negative(self, image):
        """Apply negative effect"""
        return ImageOps.invert(image.convert('RGB'))
    
    def _apply_sketch(self, image):
        """Apply sketch effect"""
        gray = image.convert('L')
        edges = gray.filter(ImageFilter.FIND_EDGES)
        sketch = ImageOps.invert(edges)
        return sketch.convert('RGB')
    
    def _apply_colorswap(self, image):
        """Swap color channels (RGB -> GBR)"""
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        r, g, b = image.split()
        swapped = Image.merge('RGB', (g, b, r))
        return swapped
    
    def take_photo(self, resolution, effect="normal"):
        """
        Take a photo with specified resolution and effect
        
        Args:
            resolution: tuple (width, height)
            effect: string effect name
        """
        try:
            config = self.camera.create_still_configuration(
                main={"size": resolution}
            )
            self.camera.configure(config)
            self.camera.start()
            
            time.sleep(2)
            
            image_array = self.camera.capture_array()
            
            image = Image.fromarray(image_array)
            
            if effect in self.effects:
                image = self.effects[effect](image)
            else:
                print(f"Warning: Unknown effect '{effect}', using normal")
                image = self.effects['normal'](image)
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            resolution_str = f"{resolution[0]}x{resolution[1]}"
            filename = f"photo_{timestamp}_{resolution_str}_{effect}.jpg"
            filepath = os.path.join('photos', filename)
            

            exif_dict = {
                "0th": {
                    256: resolution[0],  
                    257: resolution[1], 
                    270: f"Captured with resolution {resolution_str}, effect: {effect}",  
                    272: "PiCamera2", 
                    306: timestamp.replace('_', ':').replace('-', ':'), 
                }
            }
            
            image.save(filepath, quality=95)
            
            print(f"✓ Photo saved: {filename}")
            print(f"  Resolution: {resolution_str}")
            print(f"  Effect: {effect}")
            print(f"  Timestamp: {timestamp}")
            
            self.camera.stop()
            return filepath
            
        except Exception as e:
            print(f"Error taking photo: {e}")
            if self.camera.started:
                self.camera.stop()
            return None
    
    def test_resolutions(self):
        """Test multiple resolutions with normal effect"""
        resolutions = [
            (1920, 1080),  
            (1280, 720),  
            (640, 480)     
        ]
        
        print("Testing different resolutions...")
        print("=" * 40)
        
        for resolution in resolutions:
            print(f"\nCapturing at {resolution[0]}x{resolution[1]}...")
            self.take_photo(resolution, "normal")
            time.sleep(1) 
        
        print("\n✓ Resolution test complete!")
    
    def test_effects(self):
        """Test different effects at 1280x720 resolution"""
        effects = ['normal', 'negative', 'sketch', 'colorswap']
        resolution = (1280, 720)
        
        print("Testing different effects...")
        print("=" * 40)
        
        for effect in effects:
            print(f"\nApplying '{effect}' effect...")
            self.take_photo(resolution, effect)
            time.sleep(1) 
        
        print("\n✓ Effects test complete!")
    
    def demo_all(self):
        """Demonstrate all combinations of resolutions and effects"""
        resolutions = [(1920, 1080), (1280, 720), (640, 480)]
        effects = ['normal', 'negative', 'sketch', 'colorswap']
        
        print("Starting comprehensive photo demo...")
        print(f"Will capture {len(resolutions) * len(effects)} photos")
        print("=" * 50)
        
        photo_count = 0
        total_photos = len(resolutions) * len(effects)
        
        for resolution in resolutions:
            for effect in effects:
                photo_count += 1
                print(f"\n[{photo_count}/{total_photos}] Capturing {resolution[0]}x{resolution[1]} with {effect} effect...")
                self.take_photo(resolution, effect)
                time.sleep(2) 
        
        print(f"\n🎉 Demo complete! {total_photos} photos captured in 'photos' folder")

def main():
    """Main execution function"""
    controller = CameraController()
    
    print("PiCamera2 Photo Capture System")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Test different resolutions")
        print("2. Test different effects") 
        print("3. Take single photo (custom)")
        print("4. Run full demo")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            controller.test_resolutions()
        elif choice == '2':
            controller.test_effects()
        elif choice == '3':
            print("\nAvailable resolutions:")
            print("1. 1920x1080 (Full HD)")
            print("2. 1280x720 (HD)")
            print("3. 640x480 (VGA)")
            
            res_choice = input("Select resolution (1-3): ").strip()
            res_map = {'1': (1920, 1080), '2': (1280, 720), '3': (640, 480)}
            
            if res_choice in res_map:
                resolution = res_map[res_choice]
                
                print("\nAvailable effects:")
                print("1. normal")
                print("2. negative") 
                print("3. sketch")
                print("4. colorswap")
                
                effect_choice = input("Select effect (1-4): ").strip()
                effect_map = {'1': 'normal', '2': 'negative', '3': 'sketch', '4': 'colorswap'}
                
                if effect_choice in effect_map:
                    effect = effect_map[effect_choice]
                    controller.take_photo(resolution, effect)
                else:
                    print("Invalid effect choice")
            else:
                print("Invalid resolution choice")
        elif choice == '4':
            controller.demo_all()
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice, please try again")

if __name__ == "__main__":
    main()
