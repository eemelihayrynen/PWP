# Meeting notes from discussion after deadline 4

- An entrypoint must be added to the hypermedia API (e.g. MovieCollection)
  - entrypoint /api/ added
- Relationships in the hypermedia design must be retought between movie collection and actor collection, and also streaming collection as whole as it is isolated
  - fixed in the code
- Whole implementation for the hypermedia is no done yet
  - basic hypermedia is now implemented
- Implementation and documentation of streaming collection and streaming item is WIP
  - mostly done
- Response 400 is missing from implementation and documentation (invalid schema)
  - added
- The resources are not separated in the documentation for some reason
  - added missing tags
- Wiki in github needs to be filled better in all chapters to match the implementation
  - many improvements
- Consider creating a spider for IMDB to populate the database. This might pass as the required auxiliary service
  - IMBD did not provide live api, using offline data download
- Start to consider the client needed for the final deadline.
  - rudimentary client implemented
- The project structure should be managed better. Not everything in single file.
  - TBD
- Check the code quality with pylint.
  - many improvements done
- Add comments to code where needed.
- If code has been taken from somewhere, put the source to comments (e.g. from exercises, one general comment is enough)
  - done
