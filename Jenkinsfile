pipeline {
    agent none
    stages {
        stage('Collect') {
            matrix {
                agent {
                    label "${BUILD_PLATFORM}-${BUILD_ARCH}-${SLAVE_TYPE}"
                }
                axes {
                    axis {
                        name 'BUILD_PLATFORM'
                        values 'ubuntu-focal', 'debian-bullseye', 'vs2015', 'vs2019'
                    }
                    axis {
                        name 'BUILD_ARCH'
                        values 'x86', 'amd64'
                    }
                    axis {
                        name 'SLAVE_TYPE'
                        values 'test', 'build'
                    }

                }
                excludes {
                    exclude {
                        axis { //ubuntu does no longer support 32 bit builds
                            name 'BUILD_PLATFORM'
                            values 'ubuntu-focal'
                        }
                        axis {
                            name 'BUILD_ARCH'
                            values 'x86'
                        }
                    }
                }
                stages {
                    stage('Clean') {
                        steps {
                            script {
                                if (isUnix()) {
                                    sh 'git clean -fxd'
                                }
                                else {
                                    bat 'git clean -fxd'
                                }
                            }
                        }
                    }
                    stage('Print Versions') {
                        steps {
                            script {
                                if (isUnix()) {
                                    sh script: """
                                              export PATH=$PATH:/home/jenkins/.local/bin
                                              ./show_versions.py --output ${BUILD_PLATFORM}-${BUILD_ARCH}-${SLAVE_TYPE}-versions.txt
                                              """
                                }
                                else {
                                    bat "python show_versions.py --output ${BUILD_PLATFORM}-${BUILD_ARCH}-${SLAVE_TYPE}-versions.txt"
                                }

                                archiveArtifacts artifacts: "${BUILD_PLATFORM}-${BUILD_ARCH}-${SLAVE_TYPE}-versions.txt"
                            }
                        }
                    }
                }
            }
        }
        stage('Collate') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'git clean -fxd'
                    }
                    else {
                        bat 'git clean -fxd'
                    }
                }

                copyArtifacts projectName: '${JOB_NAME}',
                              selector: specific('${BUILD_NUMBER}')

                script {
                    if (isUnix()) {
                        sh script: """
                                   export PATH=$PATH:/home/jenkins/.local/bin
                                   ./generate_summary.py
                                   """
                    }
                    else {
                        bat "python generate_summary.py"
                    }
                }
            }
        }
    }
}
