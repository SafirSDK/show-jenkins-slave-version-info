pipeline {
    agent none
    stages {
        stage('Collect') {
            matrix {
                agent {
                    label "${BUILD_PLATFORM}-${BUILD_ARCH}-build"
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
                                    sh "show_versions.py --output ${BUILD_PLATFORM}-${BUILD_ARCH}-versions.txt"
                                }
                                else {
                                    bat "show_versions.py --output ${BUILD_PLATFORM}-${BUILD_ARCH}-versions.txt"
                                }

                                archiveArtifacts artifacts: "${BUILD_PLATFORM}-${BUILD_ARCH}-versions.txt", fingerprint: true
                            }
                        }
                    }
                }
            }
        }
    }
}
