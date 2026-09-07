# frozen_string_literal: true

require 'tty-table'
require_relative 'error_handler'

module SacctApi
  # TTY table renderer
  class Renderer
    EFFICIENCY_HEADERS = ['Job count', 'Queue Time(avg)', 'Run time(Avg)', 'CPU eff', 'Mem Eff'].freeze
    SHAPE_HEADERS = ['Type', 'Count', 'Avg CPU', 'Avg Node', 'Avg CPU/Node'].freeze
    QUOTA_HEADERS = ['Filesystem', 'Used Bytes', 'Quota Bytes', 'Limit Bytes', 'Used Files', 'Quota Files',
                     'Limit Files'].freeze

    def initialize(data)
      @data = data
    end

    def self.render(data)
      new(data).render
    end

    def render
      value = check_if_json_ok
      value.positive? ? ErrorHandler.print(value, @data) : render_values
    end

    private

    def render_values
      puts efficiency_table, job_table if valid_data?
      quota = @data[:quota_filesystem] || @data['quota_filesystem']
      return if quota.nil? || quota == 'none'

      puts 'Usage Quota table', quota_table
    end

    def valid_data?
      days_back = @data[:days_back] || @data['days_back']
      days_back.is_a?(Hash) && days_back.values.any? { |val| valid_entry?(val) }
    end

    def valid_entry?(val)
      return false if val.nil? || (val.is_a?(Hash) && (val.key?(:Error) || val.key?('Error')))

      !val.to_s.downcase.eql?('none')
    end

    def check_if_json_ok
      return 1 if @data.nil?
      return 2 if @data.key?(:Error)
      return 3 if @data.dig(:last, :submit) =~ /^Not within \d+ days$/

      0
    end

    def title(table, multiple)
      msg = multiple ? "#{table} table over range" : "#{table} table for #{@data[:days_back].keys.first} days"
      puts msg
    end

    def table_render(headers, rows, multiline: false, style: :unicode)
      return '' if rows.empty?

      table = TTY::Table.new(header: headers, rows: rows)
      border_opts = multiline ? { separator: :each_row } : {}

      puts table.render(style, multiline: multiline, border: border_opts, padding: [0, 1, 0, 0])
      puts "\n"
    end

    def efficiency_table
      multiple = @data[:days_back].size > 1
      title('Efficency', multiple)

      headers = multiple ? ['Days'] + EFFICIENCY_HEADERS : EFFICIENCY_HEADERS
      rows = @data[:days_back].map do |fs_path, fs_info|
        row = [fs_info.dig(:jobs, :count), fs_info.dig(:jobs, :average_queue), fs_info.dig(:jobs, :average_time),
               fs_info.dig(:efficiency, :"cpu%"), fs_info.dig(:efficiency, :"mem%")]
        multiple ? [fs_path.to_s] + row : row
      end

      table_render(headers, rows)
    end

    def job_table
      multiple = @data[:days_back].size > 1
      title('Job Shape', multiple)

      if multiple
        headers = ['Days back', 'Job Shapes Summary']
        rows = @data[:days_back].map { |path, info| [path.to_s, job_table_individual(info, false)] }
        table_render(headers, rows, multiline: true, style: :unicode)
      else
        job_table_individual(@data[:days_back].values.first, true)
      end
    end

    def job_table_individual(passed_data, single)
      shapes = passed_data.dig(:jobs, :shapes)
      return '-' if shapes.nil? || shapes.empty?

      rows = shapes.map do |fs_path, fs_info|
        [
          fs_path.to_s, fs_info[:count], fs_info.fetch(:avg_cpu, '-'),
          fs_info.fetch(:avg_node, '-'), fs_info.fetch(:avg_cpu_per_node, '-')
        ]
      end

      table_render(SHAPE_HEADERS, rows, style: single ? :unicode : :basic)
    end

    def quota_table
      rows = @data[:quota_filesystem].map do |fs_path, fs_info|
        [
          fs_path.to_s, fs_info.dig(:blocks, :used_bytes), fs_info.dig(:blocks, :quota_bytes),
          fs_info.dig(:blocks, :limit_bytes), fs_info.dig(:files, :used), fs_info.dig(:files, :quota),
          fs_info.dig(:files, :limit)
        ]
      end

      table_render(QUOTA_HEADERS, rows)
    end
  end
end
