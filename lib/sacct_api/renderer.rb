# frozen_string_literal: true

require 'tty-table'

module SacctApi
  # TTY table renderer
  class Renderer
    def initialize(data)
      @data = data
    end

    def self.render(data)
      new(data).render
    end

    def render
      value = check_if_json_ok 
      value > 0 ? error_handler(value) : table_render
    end

    private

    def error_handler(code)
      errors = ["Error handler failed","API down","HTTPS error","No recent access"]
      reason = ["The error handler activated when data was ok","There was no valid connection to the API, or the API failed to return data","See HTTPS error","The user did not have any recent acccesses"]
      if code == 2
        errors[2] = @data[:Error]
        reason[2] = @data[:Reason]
      puts 'Error: ' + errors[code]
      puts 'Reason: ' + reason[code]

    def table_render
      quota_table if @data.key?(:quota_filesystem)

    def check_if_json_ok
      return 1 if data.nil #API down
      return 2 if data.key?("Error") #Error in request
      return 3 if data.dig(:last,:submit) =~ /^Not within \d+ days$/ #Did not get any data
      return 0 #Ok, data exists

    def quota_table
      fs_path, fs_info = @data[:quota_filesystem].first

      headers = ['Filesystem', 'Used Bytes', 'Quota Bytes', 'Limit Bytes', 'Used Files', 'Quota Files', 'Limit Files']
      row = [
        fs_path.to_s,
        fs_info.dig(:blocks, :used_bytes),
        fs_info.dig(:blocks, :quota_bytes),
        fs_info.dig(:blocks, :limit_bytes),
        fs_info.dig(:files, :used),
        fs_info.dig(:files, :quota),
        fs_info.dig(:files, :limit)
      ]

      table = TTY::Table.new(
        header: headers,
        rows: [row]
      )

      puts table.render(:ascii)
    end
  end
end