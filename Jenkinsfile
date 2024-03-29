#!groovy

pipeline {

  // agent defines where the pipeline will run.
  agent {
    label "ndw1757"
  }
  environment {
    HLM_PYTHON= "C:/HLM_PV_Import/python.exe"
    VENV_PATH= "C:/HLM_PV_Import/myvenv"
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
            %HLM_PYTHON% -m venv %VENV_PATH%
            call "%VENV_PATH%\\Scripts\\activate.bat"
            python -m pip install -r requirements.txt
            python -m pip install unittest-xml-reporting
        """
      }
    }

    stage("Run Tests") {
      steps {
        echo "Branch: ${env.BRANCH_NAME}"
        checkout scm
        bat """
            call "%VENV_PATH%\\Scripts\\activate.bat"
            python setup_jenkins_settings_file.py
            coverage run -m xmlrunner discover tests -o test_results
            coverage xml -o test_results/coverage.xml
        """
      }
    }
    

    stage("Run Pylint") {
      steps {
        bat """
            call "%VENV_PATH%\\Scripts\\activate.bat"
            python -m pylint ServiceManager HLM_PV_Import --output-format=parseable --reports=no module --exit-zero > pylint.log
            echo pylint exited with %errorlevel%
         """
        echo "linting Success, Generating Report"
        recordIssues enabledForFailure: true, aggregatingResults: true, tool: pyLint(pattern: 'pylint.log')
      }
    }
  }
  post {
    always {
      junit "test_results/*.xml"
      cobertura coberturaReportFile: 'test_results/coverage.xml'
    }
  }
}
