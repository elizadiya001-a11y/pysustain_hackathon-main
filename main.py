import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from google import genai
from PIL import Image

class SoilAdvisorApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 1. Inputs
        self.ph_input = TextInput(hint_text="Enter Soil pH (e.g. 6.5)", input_filter='float')
        self.crop_input = TextInput(hint_text="Enter Current Crop (e.g. Wheat)")
        self.layout.add_widget(self.ph_input)
        self.layout.add_widget(self.crop_input)
        
        # 2. Action Button
        self.submit_btn = Button(text="Analyze & Recommend", background_color=(0.2, 0.7, 0.3, 1))
        self.submit_btn.bind(on_press=self.analyze_data)
        self.layout.add_widget(self.submit_btn)
        
        # 3. Output Display
        self.result_label = Label(text="Results will appear here.", text_size=(400, None))
        self.layout.add_widget(self.result_label)
        
        return self.layout

    def analyze_data(self, instance):
        client = genai.Client(api_key="YOUR_GEMINI_API_KEY")
        
        prompt = f"""
        Farmer Inputs:
        - Soil pH: {self.ph_input.text}
        - Current Crop: {self.crop_input.text}
        
        Task: Identify optimal crops based on standard soil datasets and compare yields. Provide a concise summary.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        self.result_label.text = response.text

if __name__ == '__main__':
    SoilAdvisorApp().run()