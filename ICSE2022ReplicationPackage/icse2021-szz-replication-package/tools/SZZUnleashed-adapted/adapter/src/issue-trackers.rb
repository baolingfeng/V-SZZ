require 'code-assertions'
require 'nokogiri'
require 'open-uri'
require 'sanitize'
require 'json'
require 'time'
require 'cgi'

class Issue
    attr_accessor   :url
    attr_accessor   :hash
    attr_accessor   :creation_date
    attr_accessor   :resolution_date
    attr_accessor   :commit_date
        
    @@id = 0
    
    def initialize(url, creation_date)
        @id = @@id
        @url            = url
        @creation_date  = creation_date
        
        @@id += 1
    end
    
    def id
        "FAKEISSUE-#@id"
    end
    
    def to_json
        JSON.generate(self.to_h)
    end
    
    def to_h
        data = {
            hash: @hash,
            creationdate: @creation_date,
            resolutiondate: @resolution_date,
            commitdate: @commit_date
        }
        
        return data
    end
end

class IssueTracker
    @@implementations = nil
    
    def initialize
    end
    
    def fetch(url)
        URI.open(url) do |f|
            raw = f.read
            document = Nokogiri::HTML(raw)
            return self.extract_info(url, raw, document)
        end
    end
    
    def extract_info
        raise "extract_info not implemented yet for " + self.class
    end
    
    def handles?(url)
        return false
    end
    
    def self.handler_for(url)        
        matching = self.implementations.select { |implementation| implementation.handles?(url) }
        assert("There must be at most an implementation for #{url}; #{matching.size} found (#{matching}).") { matching.size < 2 }
        
        raise NoIssueTrackerHandlerException, "No issue tracker matching #{url}" if matching.size == 0
        return matching[0]
    end
    
    def self.implementations
        unless @@implementations
            @@implementations = []
            ObjectSpace.each_object(Class).select { |klass| klass < self }.each do |klass|
                @@implementations << klass.new
            end
        end
        
        return @@implementations
    end
    
    class NoIssueTrackerHandlerException < Exception
    end
end

class Jira < IssueTracker
    def handles?(url)
        return false unless url
        
        return url.match?(/^https?:\/\/jira\./) || 
               url.match?(/^https?:\/\/[^\/]+\/jira\//) ||
               url.match?(/^https?:\/\/bugreports\.qt\.io\//) ||
               url.match?(/^https:\/\/issues\.redhat\.com\//)
    end
    
    def extract_info(url, raw, html)
        creation_date = Time.parse(html.css("#created-val > time")[0].attr('datetime'))
        
        return Issue.new(url, creation_date)
    end
end

class Bugzilla < IssueTracker
    def handles?(url)
        return false unless url
        
        return url.match?(/show\_bug\.cgi\?/) ||
               url.match?(/^https?:\/\/bugzilla\./)
    end
    
    def extract_info(url, raw, html)
        scanned = Sanitize.clean(raw).scan(/Reported:\s*([0-9]{4}\-[0-9]{2}\-[0-9]{2} [0-9]{2}:[0-9]{2} [a-zA-Z+0-9]+) by/).flatten[0]
        creation_date = Time.parse(scanned)
        
        return Issue.new(url, creation_date)
    end
end

class Launchpad < IssueTracker
    def handles?(url)
        return false unless url
        
        return url.match?(/^https?:\/\/bugs\.launchpad\.net/)
    end
    
    def extract_info(url, raw, html)
        creation_date = Time.parse(html.css("#registration > span")[0].attr('title'))
       
        return Issue.new(url, creation_date)
    end
end

class GitHub < IssueTracker
    def handles?(url)
        return false unless url
        
        return url.match?(/^https?:\/\/(?:www\.|)github\.com/)
    end
    
    def extract_info(url, raw, html)
        creation_date = Time.parse(html.css("#partial-discussion-header relative-time").attr('datetime'))
        
        return Issue.new(url, creation_date)
    end
end

class GitLab < IssueTracker
    def handles?(url)
        return false unless url
        
        return url.match?(/^https?:\/\/(?:www\.|)gitlab\.com/) ||
               url.match?(/^https?:\/\/gitlab\./) ||
               url.match?(/https?:\/\/framagit\.org\//) ||
               url.match?(/https?:\/\/dev.ib.pl\//)
    end
    
    def extract_info(url, raw, html)
        creation_date = Time.parse(html.css(".detail-page-header .js-timeago").attr('datetime'))
        
        return Issue.new(url, creation_date)
    end
end

class SourceForge < IssueTracker
    def handles?(url)
        return false unless url
        
        return url.match?(/^https?:\/\/(?:www\.|)sourceforge\.net/)
    end
    
    def extract_info(url, raw, html)
        creation_date = Time.parse(html.css("#content_base > div.grid-20.pad > div.editbox > div > div:nth-child(8) > span").attr('title'))
        
        return Issue.new(url, creation_date)
    end
end

class Trac < IssueTracker
    def handles?(url)
        return false unless url
        
        return url.match?(/^https?:\/\/trac\./) ||
               url.match?(/^https?:\/\/[^\/]+\/trac\//)
    end
    
    def extract_info(url, raw, html)
        href = URI(html.css("#ticket > div.date > p:nth-child(1) > a").attr('href'))
        creation_date = Time.parse(CGI.unescape(href.query.split('&').select { |par| par.start_with?('from=') }.first.sub('from=', '')))
        
        return Issue.new(url, creation_date)
    end
end

class Monorail < IssueTracker
    def handles?(url)
        return false unless url
        
        return url.match?(/https?:\/\/bugs\.chromium\.org/)
    end
    
    def extract_info(url, raw, html)
        # NOTE It would require phantomjs and stuff, not handling for now, just raising an exception
        raise "Not supported yet"
    end
end

class Redmine < IssueTracker
    def handles?(url)
        return false unless url
        
        return url.match?(/https?:\/\/projects\.theforeman\.org\//) ||
               url.match?(/https?:\/\/(?:www\.|)redmine\.org\//)
    end
    
    def extract_info(url, raw, html)
        creation_date = Time.strptime(html.css("p.author > a:nth-child(2)").attr('title'), '%m/%d/%Y %H:%M %p')
        
        return Issue.new(url, creation_date)
    end
end

class MantisBT < IssueTracker
    def handles?(url)
        return false unless url
        
        return url.match?(/https?:\/\/tracker\.ardour\.org\//) ||
               url.match?(/https?:\/\/tracker\.freecadweb\.org\//)
    end
    
    def extract_info(url, raw, html)
        creation_date = Time.parse(html.css(".bug-date-submitted").text)
        
        return Issue.new(url, creation_date)
    end
end

class NoIssueTracker < IssueTracker
    def handles?(url)
        return url == nil
    end
    
    def fetch(url)
        return Issue.new(nil, nil)
    end
end
