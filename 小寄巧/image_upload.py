import sys, os, requests

api_smms = "https://sm.ms/api/v2/upload"
key_smms = ""

api_imgbb = "https://api.imgbb.com/1/upload"
key_imgbb = ""

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

def upload_image(file_path, host='imgbb'):
    if host == 'imgbb':
        response = requests.post(api_imgbb, files={"image": open(file_path, "rb")}, 
                                 data={"key": key_imgbb})
        if ((response.status_code == 200)):
            if (response.json()["success"]):
                return response.json()["data"]["url"]
        print("Failed to upload image.")
        return "[upload failed]"
        
    elif host == 'smms':
        response = requests.post(api_smms, headers={"Authorization": key_smms}, 
                                 files={"image": open(file_path, "rb")}, data={"format": "json"})
        if ((response.status_code == 200) & response.json()["success"]):
            return response.json()["data"]["url"]
        print("Failed to upload image:", response.json()["message"])
        return "[upload failed]"
    
def gen_cprimg(image_list):
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
    if len(sys.argv) < 2:
        while True:
            image_list = []
            image_input = input("Images to upload: ")
            while (len(image_input) > 0):
                image_input, image = read_first_path(image_input)
                image_list.append(image)
            image_list.sort()
            gen_cprimg(image_list)
    else:
        folder_path = sys.argv[1]
        if not os.path.exists(folder_path):
            print(f"The folder '{folder_path}' does not exist.")
        elif not os.path.isdir(folder_path):
            print(f"'{folder_path}' is not a folder.")
        else:
            absolute_paths = []
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    absolute_paths.append(os.path.abspath(file_path))
            absolute_paths.sort()
            gen_cprimg(absolute_paths)
  
