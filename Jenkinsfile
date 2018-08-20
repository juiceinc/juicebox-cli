#!groovy

def default_channel_name = '#ci-cd'

def CHANNEL_NAME = env.CHANNEL_NAME == null ? default_channel_name : env.CHANNEL_NAME

def projectProperties = [
  buildDiscarder(logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '30', numToKeepStr: '100')),
  [$class: 'RebuildSettings', autoRebuild: false, rebuildDisabled: false],
  parameters(
    [
        string(      defaultValue: 'master',       description: 'The branch to target', name: 'BRANCH_NAME'),
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

    stage('Build Docs') {
      steps {
      sh '''
#!/usr/bin/bash
if [ "$BRANCH_NAME" = "master" ]; then . .venv/bin/activate; cd docs; make html; fi;
'''
      }
    }
  }
post {
    always {
      sendNotifications(currentBuild.result, "$CHANNEL_NAME")
    }
  }
}
GET | 302 | ? ms | GitHub.com
GET | 200 | ? ms