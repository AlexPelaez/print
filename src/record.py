#!/usr/bin/env python3
import time
import json
import os
import threading
import signal
import queue
import sys
from datetime import datetime
from pynput import mouse, keyboard
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController, KeyCode

class InputRecorder:
    def __init__(self):
        self.recording = False
        self.events = []
        self.start_time = None
        self.mouse_listener = None
        self.keyboard_listener = None
        self.mouse_controller = MouseController()
        self.keyboard_controller = KeyboardController()
        self.recordings_dir = os.path.expanduser("~/Documents/InputRecordings")
        self.stop_key_combination = {Key.cmd, KeyCode.from_char('l')}  # Command+l
        self.current_keys = set()
        self.recording_stopped = threading.Event()
        self.save_event = threading.Event()
        
        # Create recordings directory if it doesn't exist
        if not os.path.exists(self.recordings_dir):
            os.makedirs(self.recordings_dir)
    
    def on_mouse_click(self, x, y, button, pressed):
        if not self.recording:
            return
        
        if pressed:
            event_time = time.time() - self.start_time
            self.events.append({
                'type': 'mouse_click',
                'time': event_time,
                'x': x,
                'y': y,
                'button': str(button)  # Convert button to string for better serialization
            })
            print(f"Recorded mouse click at ({x}, {y}) with {button}")
    
    def on_keyboard_press(self, key):
        if not self.recording:
            return True
        
        # Add key to current keys
        self.current_keys.add(key)
        
        # Check if stop key combination is pressed
        if all(k in self.current_keys for k in self.stop_key_combination):
            print("\nStop key combination detected (Command+L)")
            # Set flag to stop recording
            self.recording = False
            self.recording_stopped.set()
            # Schedule save operation
            threading.Thread(target=self.save_after_stop).start()
            return False  # Stop the listener
        
        try:
            event_time = time.time() - self.start_time
            char = key.char
            self.events.append({
                'type': 'keyboard_press',
                'time': event_time,
                'key': char
            })
            print(f"Recorded key press: {char}")
        except AttributeError:
            # Handle special keys
            event_time = time.time() - self.start_time
            self.events.append({
                'type': 'keyboard_special',
                'time': event_time,
                'key': str(key)
            })
            print(f"Recorded special key press: {key}")
        
        return True  # Continue listener
    
    def on_keyboard_release(self, key):
        if key in self.current_keys:
            self.current_keys.remove(key)
        return True
    
    def save_after_stop(self):
        """Handle saving the recording after stopping with Command+L"""
        # Ensure the listeners are stopped
        if self.mouse_listener and self.mouse_listener.is_alive():
            self.mouse_listener.stop()
        if self.keyboard_listener and self.keyboard_listener.is_alive():
            self.keyboard_listener.stop()
        
        print(f"Recording stopped. Recorded {len(self.events)} events.")
        
        # Save the recording
        if self.events:
            # Auto-generate a filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.recordings_dir, f"recording_{timestamp}.json")
            
            with open(filename, 'w') as f:
                json.dump(self.events, f, indent=2)
            
            print(f"Recording automatically saved to {filename}")
        
        # Signal that saving is complete
        self.save_event.set()
    
    def start_recording(self):
        if self.recording:
            print("Already recording!")
            return
        
        # Reset events
        self.recording_stopped.clear()
        self.save_event.clear()
        
        self.recording = True
        self.events = []
        self.start_time = time.time()
        self.current_keys = set()
        
        # Start listeners
        try:
            self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_keyboard_press,
                on_release=self.on_keyboard_release
            )
            
            self.mouse_listener.start()
            self.keyboard_listener.start()
            
            print("Recording started. Press Command+L to stop recording.")
        except Exception as e:
            print(f"Error starting recording: {e}")
            self.recording = False
            self.check_permissions()
    
    def stop_recording(self):
        if not self.recording:
            print("Not currently recording!")
            return
        
        # Stop recording
        self.recording = False
        self.recording_stopped.set()
        
        # Stop listeners
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        print(f"Recording stopped. Recorded {len(self.events)} events.")
        
        # Ask for a name to save the recording
        if self.events:
            self.save_recording()
    
    def save_recording(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"recording_{timestamp}"
        
        name = input(f"Enter a name for this recording (default: {default_name}): ")
        if not name.strip():
            name = default_name
        
        filename = os.path.join(self.recordings_dir, f"{name}.json")
        
        with open(filename, 'w') as f:
            json.dump(self.events, f, indent=2)
        
        print(f"Recording saved to {filename}")
    
    def list_recordings(self):
        print("\nAvailable recordings:")
        recordings = [f for f in os.listdir(self.recordings_dir) if f.endswith('.json')]
        
        if not recordings:
            print("No recordings found.")
            return []
        
        for i, rec in enumerate(recordings, 1):
            print(f"{i}. {os.path.splitext(rec)[0]}")
        
        return recordings
    
    def check_permissions(self):
        """Check for required permissions on macOS"""
        if sys.platform == "darwin":
            print("\n==== PERMISSIONS REQUIRED ====")
            print("This application requires accessibility permissions to control your mouse and keyboard.")
            print("Please follow these steps:")
            print("1. Go to System Preferences > Security & Privacy > Privacy > Accessibility")
            print("2. Click the lock icon to make changes")
            print("3. Add Terminal or your Python IDE to the list of allowed apps")
            print("4. Make sure the checkbox next to the app is checked")
            print("5. Restart this application")
            print("\nIf you already granted permissions, try running this script from a different terminal or IDE.")
            print("==============================\n")
    
    def play_recording(self, recording_name=None):
        if recording_name is None:
            recordings = self.list_recordings()
            if not recordings:
                return
            
            try:
                choice = int(input("\nEnter the number of the recording to play: "))
                if 1 <= choice <= len(recordings):
                    recording_name = recordings[choice-1]
                else:
                    print("Invalid choice.")
                    return
            except ValueError:
                print("Please enter a valid number.")
                return
        
        filename = os.path.join(self.recordings_dir, recording_name)
        if not os.path.exists(filename):
            filename = os.path.join(self.recordings_dir, recording_name + '.json')
            if not os.path.exists(filename):
                print(f"Recording '{recording_name}' not found.")
                return
        
        try:
            # Load the JSON recording file
            with open(filename, 'r') as f:
                events = json.load(f)
            
            print(f"Loaded {len(events)} events from {filename}")
            print("Playback will start in 3 seconds. Position your cursor and applications appropriately...")
            countdown_seconds = 3
            for i in range(countdown_seconds, 0, -1):
                print(f"{i}...")
                time.sleep(1)
            print("Starting playback...")
            
            # Check permissions before playback
            try:
                # Test if we can move mouse as a permission check
                current_pos = self.mouse_controller.position
                self.mouse_controller.position = current_pos
            except Exception as e:
                print(f"Error accessing mouse controller: {e}")
                self.check_permissions()
                return
            
            # Debug - tell us about the current active window/application first
            print("\nMake sure you have the correct application active and in focus before playback!")
            print("Click in the window where you want the input to be directed.")
            time.sleep(3)
            
            last_time = 0
            for event in events:
                # Sleep to maintain timing between events
                time_diff = event['time'] - last_time
                if time_diff > 0:
                    time.sleep(time_diff)
                last_time = event['time']
                
                try:
                    if event['type'] == 'mouse_click':
                        # Move mouse to position - use absolute positioning
                        x, y = float(event['x']), float(event['y'])
                        self.mouse_controller.position = (x, y)
                        # Add a small delay to ensure movement completes
                        time.sleep(0.4)
                        
                        # Press and release button
                        button_map = {
                            'Button.left': Button.left,
                            'Button.right': Button.right,
                            'Button.middle': Button.middle
                        }
                        button = button_map.get(event['button'], Button.left)
                        self.mouse_controller.press(button)
                        time.sleep(0.1)  # Small delay between press and release
                        self.mouse_controller.release(button)
                        print(f"Replayed click at ({x}, {y})")
                    
                    elif event['type'] == 'keyboard_press':
                        try:
                            # For normal character keys, use a different approach
                            key = event['key']
                            # On macOS, use a safer method by writing the character directly
                            if sys.platform == 'darwin':
                                # Write the character using the write method which is more reliable
                                self.keyboard_controller.type(key)
                                time.sleep(0.3)  # Longer delay for keyboard actions on macOS
                            else:
                                # Fall back to press/release for other platforms
                                self.keyboard_controller.press(key)
                                time.sleep(0.1)
                                self.keyboard_controller.release(key)
                            print(f"Replayed keypress: {key}")
                        except Exception as e:
                            print(f"Error replaying keypress {event['key']}: {e}")
                    
                    elif event['type'] == 'keyboard_special':
                        # Handle special keys
                        key_str = event['key']
                        key_map = {
                            'Key.space': Key.space,
                            'Key.enter': Key.enter,
                            'Key.tab': Key.tab,
                            'Key.shift': Key.shift,
                            'Key.ctrl': Key.ctrl,
                            'Key.alt': Key.alt,
                            'Key.cmd': Key.cmd,
                            'Key.backspace': Key.backspace,
                            'Key.delete': Key.delete,
                            'Key.esc': Key.esc,
                            'Key.up': Key.up,
                            'Key.down': Key.down,
                            'Key.left': Key.left,
                            'Key.right': Key.right
                            # Add other special keys as needed
                        }
                        
                        special_key = key_map.get(key_str)
                        if special_key:
                            try:
                                if key_str == 'Key.space':
                                    # For space, use the type method
                                    self.keyboard_controller.type(' ')
                                else:
                                    # For other special keys, use press and release
                                    self.keyboard_controller.press(special_key)
                                    time.sleep(0.1)  # Longer delay for special keys
                                    self.keyboard_controller.release(special_key)
                                print(f"Replayed special key: {key_str}")
                            except Exception as e:
                                print(f"Error replaying special key {key_str}: {e}")
                                
                    # Add a small delay between all events for more reliable playback
                    time.sleep(0.05)
                except Exception as e:
                    print(f"Error during playback of event: {e}")
                    print("This is likely a permissions issue.")
                    self.check_permissions()
                    return
            
            print("Playback completed.")
        
        except Exception as e:
            print(f"Error during playback: {e}")
            self.check_permissions()

def handle_keyboard_interrupt(signal, frame):
    print("\nProgram interrupted. Exiting gracefully...")
    os._exit(0)

def main():
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, handle_keyboard_interrupt)
    
    recorder = InputRecorder()
    
    # Check if running with proper permissions
    try:
        # Quick test to see if we have permission to control mouse
        test_mouse = MouseController()
        current_pos = test_mouse.position
    except Exception as e:
        print(f"Error initializing mouse controller: {e}")
        recorder.check_permissions()
    
    while True:
        print("\n===== Mac Input Recorder =====")
        print("1. Start Recording")
        print("2. Play Recording")
        print("3. Quit")
        
        try:
            choice = input("\nEnter your choice (1-3): ")
            
            if choice == '1':
                recorder.start_recording()
            elif choice == '2':
                recorder.play_recording()
            elif choice == '3':
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")
        except KeyboardInterrupt:
            print("\nProgram interrupted. Exiting gracefully...")
            break

if __name__ == "__main__":
    main()