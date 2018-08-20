#!groovy

def default_channel_name = '#ci-cd'

def CHANNEL_NAME = env.CHANNEL_NAME == null ? default_channel_name : env.CHANNEL_NAME

def projectProperties = [
  buildDiscarder(logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '30', numToKeepStr: '100')),
  [$class: 'RebuildSettings', autoRebuild: false, rebuildDisabled: false],
  parameters(
    [
        string(      defaultValue: CHANNEL_NAME,       description: 'The slack channel to use', name: 'CHANNEL_NAME'),
    ]
  ),
]

properties(projectProperties)

@Library('juiceinc-library') _

pipeline {
  agent  { label 'python-ecs' }
  stages {
    stage('Checkout') {
      steps{
        sendNotifications('STARTED', "$CHANNEL_NAME")
        checkout scm
      }
    }

    stage('Installing Prereqs') {
      steps {
        sh '''
#!/usr/bin/bash
virtualenv --no-site-packages .venv
. .venv/bin/activate
pip install -qq -U pip wheel
pip install -qq --exists-action w -r requirements-dev.txt
'''
      }
    }
    stage('Testing') {
      steps {
      sh '''
#!/usr/bin/bash
if [ "$BRANCH_NAME" = "master" ]; then . .venv/bin/activate; pytest --junit-xml=junit.xml --cov-branch --cov-report=xml --cov=juicebox_cli; fi;
'''
      }
    }
    stage('Build Docs') {
      steps {
      sh '''
#!/usr/bin/bash
if [ "$BRANCH_NAME" = "master" ]; then . .venv/bin/activate; cd docs; make html; fi;
'''
      }
    }
    stage('Publish Docs') {
      steps {
      sh '''
#!/usr/bin/bash
if [ "$BRANCH_NAME" = "master" ]; then . .venv/bin/activate; cd docs; aws s3 sync build/html s3://internal.juiceboxdata.com/projects/juicebox-cli --acl bucket-owner-full-control --delete; aws s3 sync build/html s3://docs.juiceboxdata.com/projects/juicebox-cli --acl bucket-owner-full-control --delete; fi;

'''
      }
    }
  }
post {
    always {
      archiveArtifacts '**/flake8_errors.txt, **/junit.xml, **/coverage.xml'
      warnings canComputeNew: false, canResolveRelativePaths: false, canRunOnFailed: true, categoriesPattern: '', defaultEncoding: '', excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[parserName: 'Pep8', pattern: 'flake8_errors.txt']], unHealthy: ''
      junit 'junit.xml'
      step([$class: 'CoberturaPublisher', autoUpdateHealth: false, autoUpdateStability: false, coberturaReportFile: '**/coverage.xml', failUnhealthy: false, failUnstable: false, maxNumberOfBuilds: 0, onlyStable: false, sourceEncoding: 'ASCII', zoomCoverageChart: false])
      sendNotifications(currentBuild.result, "$CHANNEL_NAME")
    }
  }
}