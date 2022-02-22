# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Author - Govindhi Venkatachalapathy govindhi@amazon.com
 
import argparse
import os
import time
import boto3
import datetime
import yaml
import sys
from sagemaker.network import NetworkConfig
from sagemaker.processing import Processor
from stepfunctions.inputs import ExecutionInput
from stepfunctions.steps.sagemaker import ProcessingStep
from stepfunctions.workflow import Workflow
from stepfunctions.steps import Chain
from sagemaker.processing import ProcessingOutput, ProcessingInput
from sagemaker import Session
from stepfunctions.steps.states import Choice
from stepfunctions.steps.states import Catch
from stepfunctions.steps.states import State
from stepfunctions.steps.choice_rule import ChoiceRule
 

INSTANCE_CFG_FILE = 'config.yml'
 
def getFailedState(id):
    fail_state = State(state_id=id, state_type="Fail")
    return fail_state
 
def createSFNProcessingJob():
    sfn_steps = []
    result = ''
    sec_group = None
    subnet_id = None
    INSTANCE_TYPE = "ml.c4.2xlarge"
    VOLUME_SIZE = 5
    MAX_RUNTIME = 7200
 
    # Create Session object
    sm_session = Session()
 
    instance_config = {}
    ecr_repo = "%s.dkr.ecr.%s.amazonaws.com" %(accountid, args.region)
 
    cntr_endpoint = "python3 -u convert_execute_notebook.py"
    cntr_image = "%s/%s" %(ecr_repo, args.cntrimage)
    s3_input = ''
    s3_output = "s3://%s" %sm_session.default_bucket()
    input = []
    cntr_arg_required = True
    container_output_path = '/opt/ml/processing/output'
 
    instance_config_file = os.path.join(args.workspace, INSTANCE_CFG_FILE)
    if os.path.exists(instance_config_file):
        with open(instance_config_file, 'r')as filerd:
            instance_config = yaml.load(filerd, Loader=yaml.FullLoader)
        print("Instance Config:%s" %instance_config)
        if 'instance_type' in instance_config:
            INSTANCE_TYPE = instance_config['instance_type']
        if 'volume_size' in instance_config:
            VOLUME_SIZE = instance_config['volume_size']
        if 'max_runtime' in instance_config:
            MAX_RUNTIME = instance_config['max_runtime']
        if 'security_groups' in instance_config:
            print("Security Config:%s" %instance_config['security_groups'])
            sec_group = instance_config['security_groups']
        if 'subnets' in instance_config:
            print("Subnets Config:%s" %instance_config['subnets'])
            subnet_id = instance_config['subnets']
        if 'container_endpoint' in instance_config:
            cntr_endpoint = instance_config['container_endpoint']
            cntr_arg_required = False
        if 's3_input' in instance_config:
            s3_input = instance_config['s3_input']
        if 's3_output' in instance_config:
            s3_output = instance_config['s3_output']
        if 'container_output' in instance_config:
            container_output_path = instance_config['container_output']
 
    nw_config = None
    if sec_group and subnet_id:
        print("There are security group %s and subnet_id %s" %(sec_group, subnet_id))
        nw_config = NetworkConfig(security_group_ids=sec_group, subnets=subnet_id )
 
    print("Network Config:%s" %nw_config)
    sagemaker_role = "arn:aws:iam::%s:role/sagemaker-role" %accountid
    processor_object = Processor(role=sagemaker_role,
                                 image_uri=cntr_image,
                                 instance_count=1,
                                 instance_type=INSTANCE_TYPE,
                                 volume_size_in_gb=VOLUME_SIZE,
                                 max_runtime_in_seconds=MAX_RUNTIME,
                                 sagemaker_session=sm_session,
                                 network_config = nw_config
                                )
    print(processor_object)
 
    # Get the default bucket for sagemaker
    output = ProcessingOutput(source=container_output_path, destination=s3_output, output_name='output_data', s3_upload_mode="Continuous")
    if s3_input:
        procinput = ProcessingInput(source=s3_input, destination="/opt/ml/processing/input", input_name="input_data")
        input = [procinput]
 
    # Create steps - ProcessingSteps
    # Get the list of notebooks from workspace
    print(args.workspace)
    notebook_workspace = os.path.join(args.workspace, 'src/notebooks')
    print(notebook_workspace)
 
    notebooks_list = []
    try:
        for nbfile in os.listdir(notebook_workspace):
            if nbfile.endswith(".ipynb"):
                notebooks_list.append(nbfile)
        notebooks_list = sorted(notebooks_list)
    except Exception as e:
        # May be notebooks not present
        notebooks_list = ["test.ipynb"]
    i = 0
    workflow_input = {}
    workflow_tags = [
        {'key': 'Application', 'value': 'SFN-Sagemaker'}]
 
    for nbfile in notebooks_list:
        job_name = os.path.splitext(nbfile)[0]
        currentDT = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        processing_job_name = "%s-%s" %(job_name, currentDT)
        print(processing_job_name)
        job_id = i+1
        input_name = "PreprocessingJobName%s" %str(job_id) 
        execution_input = ExecutionInput(
            schema={
                input_name: processing_job_name
            }
        )
        workflow_input[input_name] = processing_job_name
 
        print("Input name:%s" %input_name)
        print(execution_input)
        if cntr_arg_required:
            cntr_arg = '-n %s' %nbfile
            cntr_arg_list = cntr_arg.split(' ')
            processing_step = ProcessingStep(state_id=job_name,
                                            processor=processor_object,
                                            job_name=execution_input[input_name],
                                            inputs=input,
                                            outputs=[output],
                                            container_arguments=cntr_arg_list,
                                            container_entrypoint=cntr_endpoint.split(' ')
            )
        else:
            processing_step = ProcessingStep(state_id=job_name,
                                            processor=processor_object,
                                            job_name=execution_input[input_name],
                                            inputs=input,
                                            outputs=[output],
                                            container_entrypoint=cntr_endpoint.split(' ')
            )            
        i=i+1
        print(processing_step)
        # Goto next state when the current state is completed.
        if i < len(notebooks_list)-1:
            step_state = Choice(job_name)
            step_state.add_choice(rule=ChoiceRule.StringEquals(variable=processing_step.output()["ProcessingJobStatus"], value="Completed"),\
                next_step=notebooks_list[i])
 
        catch_state_processing = Catch(error_equals=['States.TaskFailed'],
                                       next_step=getFailedState("%s-fail" %job_name)
                                    )
        processing_step.add_catch(catch_state_processing)
        sfn_steps.append(processing_step)
 
    # Create Chain of steps
    workflow_graph = Chain(sfn_steps)
    print(workflow_graph)
    # Create Workflow object
    print(workflow_input)
    workflow_execution_input = ExecutionInput(
        schema=workflow_input
    )
    workflow_name = args.workflowname
    if not args.workflowname:
        workflow_name = "sfn-sm-workflow"
    workflow = Workflow(name=workflow_name,
                        definition=workflow_graph,
                        role='arn:aws:iam::%s:role/stepfunctions-role' %accountid,
                        client=None,
                        tags=workflow_tags)
    print(workflow)
    print(workflow.definition.to_json(pretty=True))
    try:
        print("Deleting the workflow:%s" %workflow_name)
        # workflow.delete()
        sm_arn = "arn:aws:states:us-east-1:%s:stateMachine:%s" %(accountid, workflow_name)
        client = boto3.client('stepfunctions')
        client.delete_state_machine(stateMachineArn=sm_arn)
        CURTIME = 0
        MAX_TIME_FOR_DELETION = 600 # 10 mins
        print("Please wait while the existing state machine is getting deleted...")
        while CURTIME <= MAX_TIME_FOR_DELETION:
            response = client.describe_state_machine(stateMachineArn=sm_arn)
            if response['status'] == 'DELETING':
                CURTIME = CURTIME+30
                time.sleep(30)
            else:
                break
        # Addition wait - Give some time for complete deletion
        time.sleep(60)
        print("Deleted the workflow(%s) successfully" %workflow_name)
    except Exception as e:
        print("Probably the Statemachine %s has been deleted:%s" %(workflow_name, e))
        # Ignore if deletion fails..may be workflow does not exist (already deleted)
        pass
    state_machine_arn = workflow.create()
    result = 'Workflow %s created' %state_machine_arn
 
    if args.execute:
        # Execute workflow
        execution = workflow.execute(inputs=workflow_input)
        print(execution)
        time.sleep(120)
        execution_output = execution.get_output(wait=True)
        print(execution_output)
        if execution_output:
            result = execution_output.get("ProcessingJobStatus")
        else:
            result = "Failure in execution of step functions. Please check the console for details"
        print(result)
    return result
 
def file_exist_valid(cfile):
    if not os.path.exists(cfile):
        raise argparse.ArgumentTypeError("{0} does not exist".format(cfile))
    return cfile
 
if __name__ == '__main__':
    parser = parser = argparse.ArgumentParser(description='Orechestrator for deploying ETL Notebooks using Step Functions and Sagemaker Processing Job')
    parser.add_argument('-w', '--workspace', required=True, help='Provide the workspace dir where the notebooks are located') 
    parser.add_argument('-f', '--workflowname', required=False, help='Provide a workflow name. If not provided, default will be provided')
    parser.add_argument('-k', '--accesskey', required=False, help='AWS Access Key Id')
    parser.add_argument('-s', '--secretaccess', required=False, help='AWS Secret Access Key')
    parser.add_argument('-r', '--region', required=False, help='AWS Region')
    parser.add_argument('-e', '--execute', action="store_true", help="Use this option to execute the step functions workflow after creation.\
        Do not specify this option if workflow has to be just created.")
    parser.add_argument('-i', '--cntrimage', required=True, help='Container image to be used in Sagemaker Processing job')
    args = parser.parse_args()
 
    # Set the env variables for AWS Config
    if not args.accesskey:
        args.accesskey = os.environ["AWS_ACCESS_KEY_ID"]
    if not args.secretaccess:
        args.secretaccess = os.environ["AWS_SECRET_ACCESS_KEY"]
    if not args.region:
        args.region = os.environ["AWS_DEFAULT_REGION"]
 
    client = boto3.client('sts')
    accountid = client.get_caller_identity()["Account"]

    response = createSFNProcessingJob()
    print(response)

 
 