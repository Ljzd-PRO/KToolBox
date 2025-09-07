#!/usr/bin/env python3
"""
Demonstration script for the new colorama-based progress bars
Shows the new Unicode progress bar style: ━━━╺━━━━━━━
"""

import time
import sys
from ktoolbox.progress import ProgressManager

def demo_colorama_progress():
    """Demo the new colorama-based progress bar display"""
    print("🎨 Colorama Progress Bar Demo")
    print("=" * 50)
    
    # Create progress manager with colors enabled
    manager = ProgressManager(max_workers=3, use_colors=True, use_emojis=True)
    manager.set_job_totals(10, completed=2, failed=0)
    
    print(f"Colorama available: {manager.use_colors}")
    print(f"Terminal supports colors: {manager.use_colors}")
    print()
    
    # Start display
    manager.start_display()
    
    try:
        # Create progress bars to demonstrate the new Unicode style
        pbar1 = manager.create_progress_bar("image1.jpg", total=1000)
        pbar2 = manager.create_progress_bar("video.mp4", total=5000)
        pbar3 = manager.create_progress_bar("document.pdf", total=800)
        
        # Simulate progress with different speeds
        for i in range(50):
            # Update progress bars at different rates
            pbar1.update(20)
            if i % 2 == 0:
                pbar2.update(100)
            if i % 3 == 0:
                pbar3.update(16)
            
            # Update the display
            manager.update_display()
            time.sleep(0.1)
            
            # Update job progress occasionally
            if i % 10 == 0:
                manager.update_job_progress(completed=2 + (i // 10))
        
        # Mark some as finished
        pbar1.close()
        manager.update_job_progress(completed=4)
        
        # Continue with remaining
        for i in range(30):
            pbar2.update(50)
            pbar3.update(10)
            manager.update_display()
            time.sleep(0.05)
        
        pbar2.close()
        pbar3.close()
        manager.update_job_progress(completed=10)
        
        # Show final state briefly
        time.sleep(1)
        
    finally:
        manager.stop_display()
    
    print("\n✅ Demo completed!")
    print("You should have seen:")
    print("- Pink/magenta progress bars with ━━━╺━━━━━━━ style (when colorama available)")
    print("- Gray remaining sections")
    print("- Overall job progress with visual bar")
    print("- Fallback to █░ characters when colorama not available")

if __name__ == "__main__":
    demo_colorama_progress()