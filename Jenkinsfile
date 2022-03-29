#!groovy

pipeline {

  // agent defines where the pipeline will run.
  agent {
    label "ndw1757"
  }
  environment {
    HLM_PYTHON= "C:/HLM_PV_Import/python.exe"
    CRYPTOGRAPHY_DONT_BUILD_RUST= 1
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
            call "myvenv\\Scripts\\activate.bat"
            python -m pip install -r requirements.txt
            python -m pip install unittest-xml-reporting
            python setup_jenkins_settings_file.py
            python -m xmlrunner discover tests -o test_results
        """
      }
    }

    stage("Run Pylint") {
      steps {
        bat """
            %HLM_PYTHON% -m pylint ServiceManager HLM_PV_Import --output-format=parseable --reports=no module > pylint.log
            echo pylint exited with %errorlevel%
         """
        recordIssues(
            tool: pyLint(pattern: '**/pylint.log'),
            unstableTotalAll: 1,
        )

      }
    }
  }
  post {
    always {
      junit "test_results/*.xml"
    }
  }
}
