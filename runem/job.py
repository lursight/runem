import typing

from runem.types.common import FilePathList, JobTags
from runem.types.filters import FilePathListLookup
from runem.types.runem_config import JobConfig, JobWhen


class NoJobName(ValueError):
    """The job-config does not contain a label and can't be coerced to crate one."""

    pass


class Job:
    """A class with utility functions for jobs.

    Currently these are static but eventually will be members
    """

    @staticmethod
    def get_job_tags(job: JobConfig) -> typing.Optional[JobTags]:
        """Returns the tags for this job or None if the tags key is missing.

        In practice None means:
        - get all files
        - always run job

        TODO: make a non-static member function
        """
        if "when" not in job or "tags" not in job["when"]:
            # handle the special case where we have No tags
            return None

        # have valid tags, coerce them to be a set-type and return
        when: JobWhen = job.get("when", {})
        job_tags: JobTags = when["tags"]
        return set(job_tags)

    @staticmethod
    def get_job_files(
        file_lists: FilePathListLookup, job_tags: typing.Optional[JobTags]
    ) -> FilePathList:
        """Return the list of files for the job-associated tags.

        TODO: support no files-groups being defined i.e. switch to all files
              being used (maybe).

        FIXME: this is a bad design choice that will need revisiting. I guess
               the options are to:
            1. Have file-list-tags (ugh)
            2. Keep associating tags with file-sets
            3. Add additional filtering based on cwd (ugh)

            #1 is probably the winner but we'll ponder on it before deciding.

        TODO: make a non-static member function
        """

        # default to all file-tags
        tags_for_files: typing.Iterable[str] = file_lists.keys()
        use_default_tags: bool = job_tags is None
        if not use_default_tags:
            # use whatever tags are in the config, even if empty
            assert job_tags  # for mypy
            tags_for_files = job_tags
        file_list: FilePathList = []
        for tag in tags_for_files:
            if tag in file_lists:
                file_list.extend(file_lists[tag])
        return sorted(file_list)

    @staticmethod
    def get_job_name(job: JobConfig) -> str:
        """Returns a name to use for a given job config.

        TODO: make a non-static member function
        """

        # First try one of the following keys.
        valid_name_keys = ("label", "command")
        for candidate in valid_name_keys:
            name: typing.Optional[str] = job.get(candidate, None)  # type: ignore # NO_COMMIT
            if name:
                return name

        # The try the python-wrapper address
        try:
            return f'{job["addr"]["file"]}.{job["addr"]["function"]}'
        except KeyError:
            raise NoJobName()  # pylint: disable=raise-missing-from
