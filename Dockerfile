# Django Backend Server (Serving Frontend, as well)
FROM python:3.14-bookworm as develop
ENV PYTHONBUFFERED 1
RUN mkdir /ffksk
WORKDIR /ffksk

EXPOSE 3002

# Install the postgres 16 client software
RUN sh -c 'echo "deb https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN apt update -y
RUN apt install postgresql-client-16 -y

# Install pgpass to run pg_dump password-less
ARG POSTGRES_PASSWORD
ARG POSTGRES_USER
ARG POSTGRES_DB
ARG POSTGRES_HOST
ARG POSTGRES_PORT
RUN echo "$POSTGRES_HOST:$POSTGRES_PORT:$POSTGRES_DB:$POSTGRES_USER:$POSTGRES_PASSWORD" > ~/.pgpass
RUN chmod 0600 ~/.pgpass

# Install Python packages
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv
RUN pipenv requirements > requirements.txt
RUN pip install -r requirements.txt
# Copy the repository files
COPY . ./

# Django application preparation
ARG DO_MIGRATE
RUN if [ "$DO_MIGRATE" = "true" ] ; then python manage.py migrate ; fi

ARG DO_INIT_SCRIPTS
RUN if [ "$DO_INIT_SCRIPTS" = "true" ] ; then python manage.py shell -c "from scripts.initialisation import initGroupsAndPermissions as x; x.InitGroupsAndPermissions();" ; python manage.py shell -c "from scripts.initialisation import initNecessaryUsers as x; x.initNecessaryUsers();" ; fi

ARG DEBUG_BUILD
RUN if [ "$DEBUG_BUILD" = "true" ] ; then pip install debugpy ; fi
RUN if [ "$DEBUG_BUILD" = "true" ] ; then echo "PYTHONBREAKPOINT=debugpy.breakpoint" >> /etc/environment ; fi

# Production image
FROM develop as production
RUN python manage.py collectstatic
