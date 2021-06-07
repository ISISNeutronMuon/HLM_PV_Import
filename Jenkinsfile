#!groovy

pipeline {

  // agent defines where the pipeline will run.
  agent {
    label "ndw1757"
  }
  environment {
    HLM_PYTHON= "C:/HLM_PV_Import/python.exe"
  }

  triggers {
    pollSCM('H/2 * * * *')
  }

  // The options directive is for configuration that applies to the whole job.
  options {
    buildDiscarder(logRotator(numToKeepStr:'10'))
    timeout(time: 60, unit: 'MINUTES')
    disableConcurrentBuilds()
    timestamps()
	skipDefaultCheckout(true)
    office365ConnectorWebhooks([[
                    name: "Office 365",
                    notifyBackToNormal: true,
                    startNotification: false,
                    notifyFailure: true,
                    notifySuccess: false,
                    notifyNotBuilt: false,
                    notifyAborted: false,
                    notifyRepeatedFailure: true,
                    notifyUnstable: true,
                    url: "${env.MSTEAMS_URL}"
            ]]
    )
  }

  stages {
    stage("Checkout") {
      steps {
        echo "Branch: ${env.BRANCH_NAME}"
        checkout scm
        bat """
            %HLM_PYTHON% -m venv myvenv
            myvenv\\Scripts\\activate
            echo "hello"
            %HLM_PYTHON% -m pip install -r requirements.txt
            echo "hello2"
            %HLM_PYTHON% -m unittest discover tests
        """
      }
    }
  }
}
