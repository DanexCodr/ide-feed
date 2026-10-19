Welcome back to my "Hanami, Why?" series. If you missed it, be sure to read [Hanami, Why?: Class Action](https://aaronmallen.me/writing/hanami-why-class-action) before you start this issue. Today we are going to be covering Hanami's database layer. It is important to note the use of the phrase "database layer," as Hanami does not have a traditional "model" layer like Rails does. Once again, this series is called "Hanami, **Why?**" so just as we did last time, we will cover the basics at a high level and then dive into why things are the way they are. I will warn you that I am still actively forming opinions and learning about Hanami's database layer myself. There is not a day that goes by that [Adam Lassek](https://github.com/alassek) is not feeding me some random TIL about this subject. Shout out to the [Hanakai Discord](https://discord.com/invite/KFCxDmk3JQ); it is a cool place to pick up lots of weird tips and tricks. Let us just dive right in.

## Crash Course

Hanami's database layer is composed of three primary parts: [Relations](https://hanakai.org/learn/hanami/v3.0/database/relations), [Repos](https://hanakai.org/learn/hanami/v3.0/database#repositories), and [Structs](https://hanakai.org/learn/hanami/v3.0/database#structs). Relations are essentially where you define an object's schema and relationships to other objects. They are also a great place to define scopes, or what Hanami calls [datasets](https://hanakai.org/learn/hanami/v3.0/database#datasets). Repos are a pretty straightforward representation of the [repository pattern](https://martinfowler.com/eaaCatalog/repository.html). Repos are actually totally optional in Hanami; you could very easily get by with just relations if you were so inclined. Repos do have the advantage of operating on multiple relations and I highly encourage their use. Lastly, structs are simple, frozen representations of your objects themselves. Structs are a place for you to define simple presentation logic for your objects. Let us look at an example of how you would go about utilizing Hanami's database layer.

```
ROM::SQL.migration do
  change do
    create_table :users do
      primary_key :id
      column :email, :varchar, index: { unique: true }, null: false, size: 255
      column :password_digest, null: false
      column :first_name, :text
      column :last_name, :text
      column :created_at, :timestamptz, null: false, default: Sequel.function(:now)
      column :updated_at, :timestamptz, null: false, default: Sequel.function(:now)
    end
  end
end
```

Here we have a pretty straightforward schema migration. I will not be diving into migrations very much as this is adequately covered in the [Hanami documentation](https://hanakai.org/learn/hanami/v3.0/database/migrations). I am simply including it here so that you can see the schema the `users` table has.

```
module MyApp
  module Relations
    class Users < DB::Relation
      schema :users, infer: true do
        attribute :email, Types::Normalized::EmailAddress

        associations do
          has_many :oauth_tokens
        end
      end
    end
  end
end
```

Here we have our relation. It will infer its schema directly from the users table. We are overriding the `:email` attribute to be a normalized email address. Lastly, we are associating the relation with the `oauth_tokens` table with a `has_many` relationship. ROM, of course, also supports `belongs_to` and `has_one` relationships.

Here we have our `UserRepo` with a few methods to help us find a user, and a method that allows us to create a user. You will notice we have direct access to both the `users` table and the `oauth_tokens` table in our repo.

Finally, here we have our `User` struct with a couple of nice-to-have presentation logic methods. You will notice we can access the `email` and name fields directly without having to explicitly define them in our struct.

The idea here is that your repos are the access point to the data layer. All methods within the repo **should** return one of your structs. You do this by calling `to_a` on collections and `one` on individual item queries. The command in the `create` method will also return a `User` struct. That is pretty much the whole shebang; congratulations, you now know how to use Hanami's data layer. Let us look at a tiny example of its actual use for completeness.

```
module MyApp
  module Operations
    class CreateUser < Operation
      include Deps["argon.hasher", "contracts.new_user_contract", "repos.user_repo"]

      def call(params)
        validated = step validate_params(params)
        step validate_email_is_unique(validated[:email])
        attributes = step build_payload(validated)
        user_repo.create(**attributes)
      end

      private

      def build_payload(params)
        built = params.slice(:email, :first_name, :last_name)
        built[:password_digest] = hasher.call(params[:password])
        Success(built)
      rescue Argon2::Error => e
        Failure(e)
      end

      def validate_email_is_unique(email)
        return Success() if user_repo.find_by_email(email).nil?

        Failure(:email_taken)
      end

      def validate_params(params)
        result = new_user_contract.call(params)
        result.success? ? Success(result.to_h[:user]) : Failure(result.errors.to_h)
      end
    end
  end
end
```

There you have it; notice we never reached directly for our relation. We interface purely through the repository layer. Again, this is totally optional and you are free to **just** use relations directly. We will talk about why I think that is a bad idea a little later in this issue.

## Advantages of the Repo Pattern

I will not get into all of the various [f](https://ryanbigg.com/2024/12/scoping-an-active-record-join)[o](https://steveklabnik.com/writing/active-record-considered-harmful/)[o](https://calpaterson.com/activerecord.html)[t](https://damieng.com/blog/2007/activerecord-the-ugly-design-pattern/) [g](https://reinteractive.com/articles/ActiveRecord-callbacks-considered-harmful)[u](https://destroyallsoftware.com/blog/2011/announcing-do-not-want)[n](https://blog.appsignal.com/2018/04/24/active-record-performance-the-n-1-queries-antipattern.html)[s](https://piechowski.io/post/why-is-default-scope-bad-rails/) provided to you by ActiveRecord. Instead I will show you a very simple-to-understand example of a **huge** problem solved by the repository pattern.

Alright, we have a pretty simple controller here that determines the "freshness" of an issue. Here is the situation: Product has decided that relying on `created_at` for this determination is not working out. Instead they have decided they are going to run a background job every hour and update a new field on the issue called `fresh_status`. Guess what? You now have to update all three of these call sites for this change. Imagine if this were something with dozens or even hundreds of call sites; what a huge pain in the ass. Now I know what you are thinking: "This is stupid, just use scopes, problem solved." To which I 100% agree, because scopes in Rails **are** an implementation of the repository pattern! Hanami encourages you by default to use this pattern to save future you from present you. It is awesome.

So what does this look like in Hanami? Here is the same freshness logic living where it belongs, in a repo.

Your action asks for the repo and calls it. That is it.

Now Product shows up with their shiny new `fresh_status` field. Here is the entire change.

One file. Your actions, your views, your mailers, and anything else calling `issue_repo.fresh` never know anything changed. You will also notice there is no `7.days.ago` here; Hanami does not ship with ActiveSupport, so we are doing a little plain Ruby math instead. The real win though is that nobody outside the repo even **has** `issues` to call `where` on, unless they go out of their way to ask for the relation in their `Deps`. The easy path to the database runs through a repo, so the knowledge of what "fresh" means lives in exactly one place, and it stays there. This is also why I said earlier that using relations directly is a bad idea. The moment you inject `relations.issues` into an action, you are right back to our `FreshnessController`, with the meaning of "fresh" scattered across every file that asked for it.

## Passing Persistence

There is another, sneakier problem with ActiveRecord, and it has nothing to do with how many call sites you have. Every time you hand someone an ActiveRecord object you hand them the **entire** persistence layer along with it. Take a look at this serializer.

Here we have a serializer, whose only job is to turn an issue into JSON, writing to the database and quietly firing off a query for every comment. Nothing stopped it. The serializer was handed a live record, so it can save, update, destroy, and lazy load whatever it wants, and you will not find out until you are staring at your logs at 2 AM. Now let us look at the same thing in Hanami.

```
module MyApp
  module Repos
    class IssueRepo < DB::Repo
      def find_with_comments(id)
        issues.combine(:comments).by_pk(id).one
      end
    end
  end
end

issue = issue_repo.find_with_comments(id)
issue.comments.map(&:body)
issue.update(last_viewed_at: Time.now) # => ROM::Struct::MissingAttribute
```

The repo decides **up front** what data gets loaded, and what comes back is a frozen struct. That struct cannot save itself, it cannot reach back into the database, and it certainly cannot go load more data behind your back. If you want to write something you have to go through a repo, and in Hanami that means you have to explicitly ask for one in your `Deps`. Your views, serializers, and mailers get data and nothing else. This is the whole point; the persistence layer stays in the persistence layer, and everything else gets to read.

## What I Have Learned

Unlike the last issue, where I gave you concrete things to do and things to avoid, we are going to do things slightly differently here. As I stated, I myself am still learning a lot about this aspect of Hanami applications every day. So instead of pretending to be some sort of authority on how you should structure this layer of your application, I would like to tell you a little bit about what I have learned, and some opinions I am holding **very** loosely at the moment. One of the primary friction points I have been experiencing in my adventures with Hanami is that I do not think I like the idea of exporting repositories across slices. Specifically, I am uncomfortable exporting repos that do mutations. I **strongly** feel that all mutations should go into operations. Unfortunately there is not currently a "read-only" abstraction in Hanami. Originally I experimented with query objects, but that felt awkward as nine times out of ten the query objects were just delegating to the repo. It was not a great abstraction, and it added unnecessary indirection. So what I ultimately decided to do is split my repos into two. One repo would **only** have read methods in it and it would be called `UserQueries`. The other repo would have all the `create`, `update`, and `delete` mutations and it would be called `UserMutations`. From there it is a matter of convention: `*_queries.rb` files are allowed to be exported and imported by other slices, `*_mutations.rb` are not. I even wrote a [cop](https://github.com/aaronmallen/rubocop-hanami) for this to enforce the convention. Now I am not sure if this is the way I will continue to do things going forward, but for now it seems to be working out pretty great. I have also been told that another approach to this problem is to simply duplicate the relation and struct code in both slice A and slice B and then write the specific repo methods needed for that particular slice. Again, Hanami gives you the freedom to choose how you want to structure your application.

## Rough Edges

I will admit coming from ActiveRecord straight into Sequel and ROM comes with a bit of a learning curve. There are **many** similarities; the query language does not feel foreign. However, there are many small differences as well that take time and toying to really figure out and harness. For example, instead of `MyModel.where(published: true).order(created_at: :desc)` you would need to do `my_model.where(published: true).order { created_at.desc }`. There are dozens of tiny differences in how Sequel does things compared to ActiveRecord. That being said, different does not mean **bad**. I have been able to overcome every obstacle I have run across thus far, and I have confidence you will too.

One of the other things that bothers me is the concept of timestamps is not really baked into Hanami like they are with Rails. There is no `timestamps` shortcut to call in your migrations. There are some timestamp features baked into ROM, but they are not the best. To ensure that `updated_at` gets incremented you would need to do something like this:

```
user.changeset(:update, **attrs).map(:touch).commit
```

I have two major issues with this:

1. If you forget to call map(:touch) in a mutation you are not incrementing your updated_at attribute.
2. ROM hard codes the time that gets populated to Time.now, meaning the updated_at time is whatever your server time zone is set to.

I tend to extend ROM with the following extensions:

```
require "rom/changeset"  
require "sequel"  

module MyApp  
  module Extensions  
    module ROM  
      module Changeset  
        module PipeRegistry  
          def touch(data)  
            Hash(updated_at: Sequel.function(:now)).merge(data)  
          end  
        end
      end
    end
  end
end  

ROM::Changeset::PipeRegistry.singleton_class.prepend(MyApp::Extensions::ROM::Changeset::PipeRegistry)
```

This ensures that the timestamp is whatever the database time is set to (you could alternatively use `Time.now.utc`), and it ensures every update increments the `updated_at` timestamp. I do not view this as a bad thing; I view it as a testament to how easy it is to shape Hanami into what you want it to be.

Alright, that is a wrap on Hanami's database layer. If there is one thing I hope you take away from this issue, it is that the split between relations, repos, and structs is there for a reason. Each piece has exactly one job: relations describe your data, repos decide how you get to it, and structs hand it to you without the ability to wander off and do something stupid with it. That split is what lets you change what "fresh" means in one file, and it is what keeps a serializer from writing to your database at 2 AM. As I said at the start, I am still learning about this layer every day, so if you have found a pattern that works better for you I would love to hear about it; come find me in the [Hanakai Discord](https://discord.com/invite/KFCxDmk3JQ). In the next issue we will be covering operations, the place where, as you may have guessed by now, I think all of your mutations belong. I hope to see you there!

Found a typo or want to argue about patterns? [Let me know](https://aaronmallen.me/contact).

## Responses

1. L[lemmy.bestiver.se](https://lemmy.bestiver.se/post/1403184)Oct 19, 2026
2. L[Lobsters](https://brid.gy/post/mastodon/@aaronmallen@ruby.social/117468149161746959)mastodon.socialOct 19, 2026Hanami, Why?: Model Citizens by @aaronmallen https://lobste.rs/s/ygp18d #rubyhttps://aaronmallen.me/writing/hanami-why-model-citizens ruby Hanami, Why?: Model Citizens

## Related

1. Hanami, Why?: Class ActionToday we are going to be diving into one of my absolute favorite abstractions in all of Hanami: Actions.Oct 12, 2026shares [hanakai](https://aaronmallen.me/writing/tags/hanakai) [hanami](https://aaronmallen.me/writing/tags/hanami) [ruby](https://aaronmallen.me/writing/tags/ruby)
2. Hanami, Why?: Bits & BobsA tour of Hanami's foundational abstractions, dependency injection, providers, types, and contracts, with an honest look at the rough edges of each.Oct 2, 2026shares [hanakai](https://aaronmallen.me/writing/tags/hanakai) [hanami](https://aaronmallen.me/writing/tags/hanami) [ruby](https://aaronmallen.me/writing/tags/ruby)
3. Hanami, Why?: IntroductionsI mentioned in my Hello, world! post that I built this site using Hanami. This site may seem simple on the surface; it is, after all, just a blog. However, the backend is packed with features that help me day to day. I have built a tool that lets me cross-post to both Bluesky and Mastodon. I have a private journal where I can keep notes throughout the day. There is a custom analytics engine to provide me with insights on how well my blog posts are doing. There is a messaging backend that lets readers reach me through my contact form without cluttering my inbox. I have also built a task manager that syncs with both Linear and GitHub Issues and helps me track what I need to do. Most importantly, I have built an activity feed that captures my GitHub commits, journal entries, blog posts, and tasks. It helps me answer the question "What did I do between ___ and ___ dates?", which, believe it or not, is hard for me to answer on my own, even for last week. The application is open source, and you can find it on GitHub.Sep 30, 2026shares [hanakai](https://aaronmallen.me/writing/tags/hanakai) [hanami](https://aaronmallen.me/writing/tags/hanami) [ruby](https://aaronmallen.me/writing/tags/ruby)