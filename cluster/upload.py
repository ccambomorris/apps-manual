#!/usr/bin/python3

import requests, json, os

if __name__ == '__main__':

    k8s_versions = [ "1.19.10","1.19.11","1.19.12","1.20.6","1.20.7","1.20.8","1.21.0","1.21.1","1.21.2" ]
    registry_version = "v2.3.0"
    registry_ip = "192.168.77.228"
    registry_id = "admin"
    registry_passwd = "Pass0000@"

    # Harbor root ca
    ca_crt = "/etc/docker/certs.d/192.168.77.228/ca.crt"

    project_names = []

    # image list will be uploaded
    images = [
        "k8s.gcr.io/pause:3.2",
        "k8s.gcr.io/pause:3.3",
        "k8s.gcr.io/pause:3.4.1",
        "k8s.gcr.io/pause:3.5",
        "k8s.gcr.io/coredns:1.7.0",
        "k8s.gcr.io/coredns/coredns:v1.8.0",
        "docker.io/calico/typha:v3.19.1",
        "docker.io/calico/node:v3.19.1",
        "docker.io/calico/cni:v3.19.1",
        "docker.io/calico/kube-controllers:v3.19.1",
        "docker.io/calico/pod2daemon-flexvol:v3.19.1",
        "docker.io/haproxy:2.4.2",
        "k8s.gcr.io/sig-storage/nfs-subdir-external-provisioner:v4.0.12",
        "k8s.gcr.io/metrics-server/metrics-server:v0.5.0",
        "gcr.io/kubernetes-e2e-test-images/dnsutils:1.3",
        "docker.io/nginx"
    ]

    for ver in k8s_versions:
        images.append(f"k8s.gcr.io/kube-apiserver:v{ver}")
        images.append(f"k8s.gcr.io/kube-controller-manager:v{ver}")
        images.append(f"k8s.gcr.io/kube-scheduler:v{ver}")
        images.append(f"k8s.gcr.io/kube-proxy:v{ver}")

    headers = {
        'accept': 'application/json',
        'Authorization': 'Basic YWRtaW46UGFzczAwMDBA',
        'Content-type': 'application/json',
    }

    # json data to create project
    data = {
        'project_name': '',
        'metadata': {'public': 'true'},
        'count_limit': -1,
        'storage_limit': -1
    }

    os.system('docker login --username {} --password {} {}'.format(registry_id, registry_passwd, registry_ip))

    if registry_version.startswith("v1."):
        registry_api_url = f"https://{registry_ip}/api"
    else:
        registry_api_url = f"https://{registry_ip}/api/v2.0"

    for image in list(images):
        down_image = image
        tag_image = ""
        project_name = ""

        names = image.split("/")

        if image.startswith("k8s.gcr.io") and len(names) == 2:
            project_name = "google_containers"
        else:
            if len(names) == 2:
                project_name = "library"
            else:
                project_name = names[1]

        image_names = down_image.split("/")
        # docker tag image
        tag_image = registry_ip+"/"+project_name+"/"+image_names[len(image_names)-1]

        # flag whether project is exist or not
        ns_flag = "N"
        # check project name in original image repo
        if len(project_names) > 0:
            try:
                project_names.index(project_name)
            except ValueError:
                ns_flag = "Y"
        else:
            ns_flag = "Y"

        if ns_flag == "Y":

            # check project existence
            url = registry_api_url + '/projects?project_name=' + project_name
            response = requests.head(url, headers=headers, verify=ca_crt)

            if response.status_code == 404:
                data["project_name"] = project_name
                project_names.append(project_name)

                # create new project
                url = registry_api_url + '/projects'
                response = requests.post(url, headers=headers, data=json.dumps(data), verify=ca_crt)
            else:
                project_names.append(project_name)
        print("===========================================================================================")
        print("Project Name >> " + project_name)
        print("DownLoad Image Name >> " + down_image)
        print("Tag Image Name >> " + tag_image)
        print("===========================================================================================")

        os.system('docker pull -q {}'.format(down_image))
        os.system('docker tag {} {}'.format(down_image, tag_image))
        os.system('docker push {}'.format(tag_image))

        # clean up
        os.system('docker rmi -f {}'.format(tag_image))
        os.system('docker rmi -f {}'.format(down_image))

    print("Completed")