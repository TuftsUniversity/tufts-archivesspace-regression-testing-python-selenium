
#!/usr/bin/env python3
from PIL import Image, ImageDraw
from selenium import webdriver
import os
import sys
import pandas as pd

class ScreenAnalysis:

    STAGING_URL_BASE = 'https://www.archives-dev-04.tufts.edu'

    driver = None

    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.set_up()
        self.run_tests()
        self.clean_up()

    def set_up(self):
        self.driver = webdriver.PhantomJS()

    def clean_up(self):
        self.driver.close()

    def run_tests(self):
        scenarios_df = pd.read_csv(self.csv_file)

        for index, row in scenarios_df.iterrows():
            scenario = row['Scenario']
            uri = row['Example record']
            print(f"Testing {scenario} - {uri}...")

            # Capture initial screenshots
            self.capture_screens(uri, scenario, "initial")

            input("Please refresh the site and press any key to continue...")

            # Capture post-refresh screenshots
            self.capture_screens(uri, scenario, "post_refresh")

            # Analyze differences
            self.analyze(uri, scenario)

    def capture_screens(self, uri, scenario, stage):
        staging_url = self.STAGING_URL_BASE + uri
        file_name_staging = f'screen_staging_{scenario}_{stage}_{uri.strip("/")}.png'

        self.screenshot(staging_url, file_name_staging)

    def screenshot(self, url, file_name):
        print("Capturing", url, "screenshot as", file_name, "...")
        self.driver.get(url)
        self.driver.set_window_size(1024, 768)
        screenshot_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'screenshots')
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
        self.driver.save_screenshot(os.path.join(screenshot_dir, file_name))
        print("Done.")

    def analyze(self, uri, scenario):
        initial_file = f"screenshots/screen_staging_{scenario}_initial_{uri.strip('/')}.png"
        post_refresh_file = f"screenshots/screen_staging_{scenario}_post_refresh_{uri.strip('/')}.png"
        screenshot_initial = Image.open(initial_file)
        screenshot_post_refresh = Image.open(post_refresh_file)

        columns = 60
        rows = 80
        screen_width, screen_height = screenshot_initial.size

        block_width = ((screen_width - 1) // columns) + 1 # division ceiling
        block_height = ((screen_height - 1) // rows) + 1

        for y in range(0, screen_height, block_height+1):
            for x in range(0, screen_width, block_width+1):
                region_initial = self.process_region(screenshot_initial, x, y, block_width, block_height)
                region_post_refresh = self.process_region(screenshot_post_refresh, x, y, block_width, block_height)

                if region_initial is not None and region_post_refresh is not None and region_post_refresh != region_initial:
                    draw = ImageDraw.Draw(screenshot_initial)
                    draw.rectangle((x, y, x+block_width, y+block_height), outline = "red")

        result_file = f"result_{scenario}_{uri.strip('/')}.png"
        screenshot_initial.save(result_file)
        print(f"Analysis complete. Results saved to {result_file}")

    def process_region(self, image, x, y, width, height):
        region_total = 0
        factor = 100  # sensitivity factor

        for coordinateY in range(y, y+height):
            for coordinateX in range(x, x+width):
                try:
                    pixel = image.getpixel((coordinateX, coordinateY))
                    region_total += sum(pixel)/4
                except:
                    return None

        return region_total/factor

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python regressionTest.py <input_csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    ScreenAnalysis(csv_file)
