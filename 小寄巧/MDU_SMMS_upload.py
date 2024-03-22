import sys
import requests

api_token_url = "https://sm.ms/api/v2/token"
api_upload_url = "https://sm.ms/api/v2/upload"
access_token = "" # get token from https://smms.app/home/apitoken, or though the api by running this script

def terminate():
    input("Program terminated, press enter to close window.")
    sys.exit(0)

def get_access_token_inner():
    data = {
        "username": input("username: "),
        "password": input("password: ")
    }

    response = requests.post(api_token_url, data=data)

    if ((response.status_code == 200) & response.json()["success"]):
        print("Access token: ", response.json()["data"]["token"])
        return True
    else:
        print("Failed to get access token: ", response.json()["message"])
        return False

def get_access_token():
    if (input("Invalid token, obtain token now? (y/n) ") == "y"):
        if (get_access_token_inner()):
            print("Past your token into the python file and restart.")
        elif (input("Try again? (y/n) ") == "y"):
            get_access_token()
    
    terminate()

def read_first_path(string):
    rest_sting = ""
    first_path = ""

    if (string[0] == "\""):
        second_quote = string.find("\"", 1)
        first_path = string[1:second_quote]
        if (second_quote == len(string) - 1):
            rest_sting = ""
        else:
            rest_sting = string[second_quote + 2:]
    else:
        second_space = string.find(" ", 1)
        if (second_space == -1):
            rest_sting = ""
            first_path = string
        else:
            rest_sting = string[second_space + 1:]  
            first_path = string[0:second_space]
            
    return rest_sting, first_path

def upload_image(file_path):
    headers = {
        "Authorization": access_token
    }
    files = {
        "smfile": open(file_path, "rb")
    }
    data = {
        "format": "json"
    }

    response = requests.post(api_upload_url, headers=headers, files=files, data=data)

    if ((response.status_code == 200) & response.json()["success"]):
        return response.json()["data"]["url"]
    else:
        print("Failed to upload image:", response.json()["message"])
        return "[upload failed]"
    
def gen_cprimg():
    # read inputs
    image_list = []
    image_input = input("Images to upload: ")
    while (len(image_input) > 0):
        image_input, image = read_first_path(image_input)
        image_list.append(image)
    image_list.sort()

    # upload images
    url_list = []
    print("")
    for image in image_list:
        print("Uploading image: ", image)
        url = upload_image(image)
        if (url != "[upload failed]"):
            print("Uploaded to: ", url)
        url_list.append(url)

    # Assemble output
    print("\nOutput:\n")
    output_text = "[center][comparison=Source,Encode]\n"
    for url in url_list:
        output_text += url + "\n"
    output_text += "[/comparison][/center]\n"

    output_text += "\n[cprimg=Source,Encode]\n"
    for url in url_list:
        output_text += url + "\n"
    output_text += "[/cprimg]"

    print(output_text, "\n")

if __name__ == "__main__":
    if (len(access_token) == 0):
        get_access_token()

    gen_cprimg()
    while (input("Upload more? (y/n) ") == "y"):
        gen_cprimg()

    terminate()
  