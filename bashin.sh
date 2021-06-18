POD_NAME="node-exec-$RANDOM"
NODE_NAME=$1


function cleanup {
    kubectl -n kube-system delete pod $POD_NAME
}

trap cleanup EXIT



NODE_LOOKUP=$(kubectl get node $1 -o json 2>&1)
if [[ $NODE_LOOKUP == *"not found"* ]]; then
    printf "Node '%s' Not Found\n" $NODE_NAME
    exit 1
fi


cat <<EOF | kubectl apply -f -
---
apiVersion: v1
kind: Pod
metadata:
  name: $POD_NAME
  namespace: kube-system
  labels:
    pod-id: $POD_NAME
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
    kubernetes.io/hostname: $NODE_NAME
EOF

kubectl -n kube-system wait -l pod-id=$POD_NAME --for=condition=ready pod --timeout=600s

kubectl -n kube-system exec -it $POD_NAME -- /bin/bash
