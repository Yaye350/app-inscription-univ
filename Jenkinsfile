pipeline {
    agent any

    environment {
        IMAGE_REPOSITORY = 'adamou26/task-api'
    }

    options {
        disableConcurrentBuilds()
    }

    stages {

        stage('Verification') {
            steps {
                echo 'Jenkins a récupéré le projet.'
                sh 'docker --version'
                sh 'docker run --rm python:3.12-slim python --version'
            }
        }

        stage('Installation') {
            steps {
                sh '''
                    docker run --rm \
                        --volumes-from jenkins \
                        --user 1000:1000 \
                        --workdir "$WORKSPACE" \
                        python:3.12-slim \
                        python -m pip install --no-cache-dir \
                            --target=".python-packages-${BUILD_NUMBER}" \
                            -r requirements.txt
                '''
            }
        }

        stage('Tests') {
            steps {
                sh '''
                    docker run --rm \
                        --volumes-from jenkins \
                        --user 1000:1000 \
                        --workdir "$WORKSPACE" \
                        --env "PYTHONPATH=.python-packages-${BUILD_NUMBER}" \
                        python:3.12-slim \
                        python -m pytest -v
                '''
            }
        }

        stage('Test SSH') {
            when {
                branch 'main'
            }
            steps {
                sshagent(credentials: ['task-api-vm-ssh']) {
                    sh '''
                        ssh -o StrictHostKeyChecking=no \
                            -o ConnectTimeout=10 \
                            deployer@192.168.197.134 \
                            "hostname && whoami"
                    '''
                }
            }
        }

        stage('Build') {
            steps {
                sh '''
                    IMAGE_TAG="build-${BRANCH_NAME:-manual}-${BUILD_NUMBER}"
                    IMAGE_TAG=$(printf '%s' "$IMAGE_TAG" | sed 's/[^A-Za-z0-9_.-]/-/g')

                    if [ "${BRANCH_NAME:-}" = "main" ]; then
                        docker build \
                            --tag "$IMAGE_REPOSITORY:$IMAGE_TAG" \
                            --tag "$IMAGE_REPOSITORY:$BUILD_NUMBER" \
                            --tag "$IMAGE_REPOSITORY:latest" .
                    else
                        docker build \
                            --tag "$IMAGE_REPOSITORY:$IMAGE_TAG" .
                    fi
                '''
            }
        }

        stage('Publish') {
            when {
                branch 'main'
            }

            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-task-api',
                        usernameVariable: 'DOCKERHUB_USER',
                        passwordVariable: 'DOCKERHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set +x

                        trap 'docker logout >/dev/null 2>&1 || true' EXIT

                        printf '%s' "$DOCKERHUB_TOKEN" | docker login \
                            --username "$DOCKERHUB_USER" \
                            --password-stdin

                        docker push "$IMAGE_REPOSITORY:$BUILD_NUMBER"
                        docker push "$IMAGE_REPOSITORY:latest"
                    '''
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sshagent(credentials: ['task-api-vm-ssh']) {
                    sh '''
                        ssh -o StrictHostKeyChecking=no \
                            deployer@192.168.197.134 \
                            "cd /opt/task-api && docker compose pull && docker compose up -d"
                    '''
                }
            }
        }

        stage('Smoke Test') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    curl --fail --silent --show-error \
                        http://192.168.197.134:8000/health
                '''
            }
        }

        stage('Deployment Info') {
            steps {
                echo 'Projet : task-api'
                echo "Branche : ${env.BRANCH_NAME ?: 'main'}"
                echo "Commit : ${env.GIT_COMMIT ?: 'voir le checkout Git'}"
                echo "Build Jenkins : ${env.BUILD_NUMBER}"
                echo 'Résultat : le pipeline a atteint la vérification finale.'
            }
        }

    }

    post {
        always {
            sh 'rm -rf ".python-packages-${BUILD_NUMBER}"'
        }
    }
}
