# frozen_string_literal: true

require 'bundler/setup'
require 'date'
require 'dry/cli'
require 'fileutils'
require 'yaml'

require_relative 'version'
require_relative '../config/configmanager'

module Sacct_api
  module CLI
    module Commands
      extend Dry::CLI::Registry

      class Report < Dry::CLI::Command
        desc 'Report based on flags sent to the cli'
        option :days, aliases:['-d','--date'], type: :integer, desc: 'Go back n amount of days'
        option :timespread, aliases:["-t","--times"], type: :boolean, desc: "Show 7,30,90 days"
        option :user, aliases:['-u','--username'], type: :string, desc: "Select user(leave blank for self)"
        
        def call(**opts)
          user = opts[:user].nil? ? current_user : opts[:user]
          days = opts[:days].nil? ? 30 : opts[:days]
          json = opts[:timespread] ? timespread(user) : single_time(user,days)
        end

        private
        def current_user
          Etc.getlogin || ENV['USER'] || ENV['LOGNAME'] || Etc.getpwuid(Process.uid)&.name
        rescue StandardError
          ENV['USER']
        end

        def timespread(user)
          cmd = "curl " + get_url + "/" + user
          puts cmd
          result = `#{cmd}`
          puts result
        end

        def single_time(user,days)
          cmd = "curl " + get_url + "/user/" + user + "/" + days.to_s
          puts cmd
          result = `#{cmd}`
          puts result
        end

        def get_url
          config = ConfigManager.load
          url = config['url']
          ssl = config['ssl'] ? '' : '-k '
          return ssl + url 
        end
      end
      register 'report', Report
    end
  end
end

