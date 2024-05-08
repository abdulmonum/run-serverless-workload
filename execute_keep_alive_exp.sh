#!/bin/bash

action_name="$1"
action_path="$2"
ow_path="/home/contow/openwhisk-deploy-kube"
config_file_path="/home/contow/openwhisk-deploy-kube/helm/openwhisk/templates/invoker-pod.yaml"
experiment_path="/home/contow/run_experiments"
ka_line_number_1=194
ka_line_number_2=196
keep_alives=(1 3 5 7 10 12 14 16 18 20 22 24 26 28 30 35 40 45 50 55 60 75 90 120 150)
#keep_alives=(0.1)
## Loop start {for keep-alive in keep-alive list}

for keep_alive in ${keep_alives[@]}; do
    # Tear down current openwhisk
    helm uninstall owdev -n openwhisk
    echo "Sleeping until openwhisk tears down (10 mins)"
    sleep 400
    # change keep alive parameter in ow-deploy-kube dir
    sed -i "${ka_line_number_1}s/\(value: \).*/\1\"${keep_alive}s\"/" $config_file_path
    sed -i "${ka_line_number_2}s/\(value: \).*/\1\"${keep_alive}s\"/" $config_file_path
    # Setup openwhisk
    cd $ow_path
    helm install owdev ./helm/openwhisk -n openwhisk --create-namespace -f mycluster.yaml
    # wait for openwhisk to boot up
    echo "Sleeping until openwhisk boots up (10 mins)"
    sleep 900
    cd $experiment_path
    # create ow action
    wsk -i action create $action_name $action_path --kind python:3.11
    # create dir and log files
    mkdir "${action_name}_${keep_alive}"
    activation_log_path="${action_name}_${keep_alive}/activation.log"
    pods_log_path="${action_name}_${keep_alive}/pods.log"
    timestamp_log_path="${action_name}_${keep_alive}/timestamp.log"
    invoker_log_path="${action_name}_${keep_alive}/invoker.log"
    controller_log_path="${action_name}_${keep_alive}/controller.log"
    scheduler_log_path="${action_name}_${keep_alive}/scheduler.log"
    touch $activation_log_path
    touch $pods_log_path
    touch $timestamp_log_path
    touch $invoker_log_path
    touch $controller_log_path
    touch $scheduler_log_path
    controller_pod="owdev-controller-0"
    scheduler_pod="owdev-scheduler-0"

    invoker_list=($(kubectl get pods -A | grep owdev-invoker | awk '{print $2}'))

    # Iterate over the list and print each value separately
    for invoker_name in "${invoker_list[@]}"; do
        echo "$invoker_name"
    done

    # run experiment
    echo "Starting experiment for keep alive ${keep_alive}"
    python3 run_workload.py $timestamp_log_path $pods_log_path $activation_log_path
    kubectl logs $controller_pod -n openwhisk > $controller_log_path
    kubectl logs $scheduler_pod -n openwhisk > $scheduler_log_path
    for invoker_name in "${invoker_list[@]}"; do
        kubectl logs $invoker_name -n openwhisk >> $invoker_log_path
    done
    #kubectl logs owdev-invoker-0 -n openwhisk | grep float > $invoker_log_path
done

echo "All measurements completed"




# Setup openwhisk

# Wait for openwhisk to bootup (15 mins)

# create action

# create dir for that keep alive

# create log files in that dir

# run workload


