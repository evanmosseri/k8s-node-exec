import random
import string

import kopf
import kubernetes.client
from kubernetes.client.rest import ApiException
import yaml


@kopf.on.create('root.shell', 'v1', 'rootshells')
def create_fn(spec, **kwargs):
    host_node = kwargs["body"]["spec"]["hostnode"]
    print(f"Creating at {host_node}")
    random_str = ''.join(random.choices(string.ascii_lowercase, k=6))
    pod_name = f"node-exec-{random_str}"
    doc = yaml.safe_load(f"""
apiVersion: v1
kind: Pod
metadata:
  name: {pod_name}
  namespace: kube-system
  labels:
    pod-id: {pod_name}
spec:
  restartPolicy: Never
  terminationGracePeriodSeconds: 0
  hostPID: true
  hostIPC: true
  hostNetwork: true
  tolerations:
  - operator: Exists
  containers:
  - name: shell
    image: docker.io/alpine:3.9
    securityContext:
      privileged: true
    command:
    - nsenter
    args:
    - "-t"
    - '1'
    - "-m"
    - "-u"
    - "-i"
    - "-n"
    - sleep
    - '14000'
  nodeSelector:
    kubernetes.io/hostname: {host_node}
    """)

    # Make it our child: assign the namespace, name, labels, owner references, etc.
    kopf.adopt(doc)

    api = kubernetes.client.CoreV1Api()
    try:
        deployment = api.create_namespaced_pod(namespace=doc['metadata']['namespace'],
                                               body=doc)
        # Update the parent's status.
        return {'children': [deployment.metadata.uid]}
    except ApiException as e:
        print("Exception when calling AppsV1Api->create_namespaced_deployment: %s\n" % e)


@kopf.on.delete('root.shell', 'v1', 'rootshells')
def delete_fn(spec, **kwargs):
    pass
