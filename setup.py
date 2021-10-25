from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(name='aliot',
          author=['Mathis Laroche', 'Enric Soldevila'],
          version='0.1.0',
          description='python IOT library compatible with the ALIVE ecosystem',
          packages=find_packages(
              include=['aliot.', 'aliot.*']),
          install_requires=[
              'msgpack',
              'schedule',
              'websocket'
          ],
          setup_requires=['flake8', 'autopep8']
          )
