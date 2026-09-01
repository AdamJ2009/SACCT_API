# frozen_string_literal: true

require_relative 'sacct_api/version'
require_relative 'sacct_api/cli'

# Primary namespace for the Sacctapi gem.
# Handles json outputs
module Sacct_api
  class Error < StandardError; end
end