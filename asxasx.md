[![DataAnnotation](https://dwuve4jqqfp9f.cloudfront.net/assets/da-logo-white-845221e8f236c8272466b016fd4cdd741a95c94e10fa16004eaf6d3856bf9662.svg)](https://app.dataannotation.tech/?task_response_id=b97e9400-838c-4775-a857-b4a8738c2d29)




* [Work on projects](https://app.dataannotation.tech/workers/projects)
* [Transfer Funds](https://app.dataannotation.tech/workers/payments)
* [Refer & Earn](https://app.dataannotation.tech/workers/referrals)
* [Inbox

  2](https://app.dataannotation.tech/workers/inbox)

* [David Nielsen](https://app.dataannotation.tech/workers/tasks/4ca6d484-3e71-4b2e-9453-10b6da41d85b?task_response_id=b97e9400-838c-4775-a857-b4a8738c2d29#)

1. [Projects](https://app.dataannotation.tech/workers/projects)
2. Prompt Writing Lab 🧪 - Periodic Refresher

Collapse Instructions

## About the refresher

One of the most important skills on the platform is being able to write detailed, creative prompts that meet a given set of project requirements. Workers who excel at doing so are more likely to receive access to new projects and opportunities. This refresher offers you the chance to sharpen your prompt writing skills in a relaxed environment. You won't be evaluated or penalized for your work here - it's just practice! The refresher is given to every worker, so it's not an indication that you're doing anything wrong. It's optional, but encouraged. The refresher will stay on your dashboard until you submit it, so you can come back to it at any time. If you wish to complete it multiple times for practice, you can simply exit without submitting once you're done.

In this refresher, you will be given various challenges and guidelines on what type of prompt to write. You will have access to 2 LLMs for each prompt; the first will generate a response to your prompt, and the second will give you feedback on ways to improve your prompt. You will use the LLM feedback to help you iteratively build your perfect prompt. It is recommended to generate a response to your prompt each time you make changes so that you can observe the evolution of the responses due to your improvements. Note that the feedback bots may not always be perfect!

The guidelines given in this refresher are generic and not tailored towards any one specific project. **Any specific instructions given to you on a project will ALWAYS take priority over what you see here.**

**Assume that the models have a cutoff date of April 2024, so do not ask for any information past the cutoff date.**

You may complete this refresher in any language you choose.

### Challenge #1 - Adding natural constraints

Constraints add complexity to the prompt by letting the model know something it must (or must not) do in order to deliver a satisfactory response. Constraints can be generally classified as either **explicit** or **implicit**.

##### Good constraints:

*Explicit*: The constraint is directly stated in the prompt. Ex:

* "Give me 5 recipes for homemade meatloaf. **Each recipe should be low in sodium.**"
* "List some of the most popular cars from 2022. **Only mention luxury models with greater than 200 hp**."
* "Compare the pros and cons of buying an Xbox vs buying a PlayStation. **Don't actually mention the price, though.**"

*Implicit*: The constraint is not directly stated in the prompt, but can be inferred from something else that is directly stated. Ex:

* "**I've never been skiing before**. Recommend some good ski resorts in Vancouver".

  + Explanation: It is implied that all ski resorts provided should offer beginner-friendly options, even though the user doesn't explicitly request this.
* "What's something tasty I can make with milk, eggs, butter, sugar, and flour? **I have to leave for work soon.**"

  + Explanation: It is implied that any food recommended should be quick to make. The model shouldn't recommend baking a cake, which takes time. Waffles or pancakes would be more suitable.
* "**I'm a lifelong Cleveland Browns fan,**butI'll be spending a year in Baltimore for a job and I'd like to check out the NFL stadium while I'm there. Can you help me find a good game to go to?"

  + Explanation: Since the user says they are a Cleveland Browns fan, the model should try to recommend a day when the Browns are in Baltimore.

##### Bad constraints:

Note that an added statement such as "I've never been skiing before" or "I'm a lifelong Cleveland Browns fan" is only considered a constraint if it has some relevance to the prompt itself. Consider the following examples:

* "I've never been skiing before. What's the formula to find the surface area of a sphere?"

  + Explanation: The fact that the user has never been skiing before is irrelevant to finding the surface area of a sphere, so this isn't a constraint. It has no impact on the model's response.
* "I'm a lifelong Cleveland Browns fan. Can you tell me what tools were common during the Mesolithic Era?"

  + Explanation: Once again, there is no connection between these two things.

Avoid writing constraints that sound unnatural or contrived, such as:

❌ "Write a poem about the sun. The poem should be exactly 78 words."

❌ "Briefly summarize the history of the Ottoman Empire. Every third word should contain either an L, S, or T."

These constraints feel random and overly specific. Although it is very likely that the model will make an error, it's not a particularly significant error since the model is responding to an unrealistic request. Contrived constraints don't simulate what a model is likely to encounter from users in the real world and are therefore unhelpful for training purposes. Better versions of these constraints would be:

✅ "Write a poem about the sun. The poem should be at least 80 words and 4 stanzas long."

✅ "Briefly summarize the history of the Ottoman Empire. Write your summary from the perspective of someone living there in the early 1900s."

Also, try to avoid ambiguous constraints such as:

❌ "Write a poem about the sun. Use odd language."

❌ Briefly summarize the history of the Ottoman Empire. Emphasize certain topics of great importance."

What is "odd language"? This is vague and subjective. Similarly, "emphasize certain topics of great importance" is difficult to rate.

🗒️ In summary, constraints should be:

* Either explicit or implicit
* Natural
* Clear enough that it is possible to determine whether a model followed the constraint or not

#### Your challenge: Write a natural sounding prompt with at least 3 explicit constraints and at least 2 implicit constraints. The content of the prompt should fall under the category Movies and Entertainment.

Process:

1. Start off by writing a prompt with 2 explicit constraints and 1 implicit constraint.
2. Then, generate a response from ResponseBot and read through it.
3. Once you've done that, add at least 1 more explicit constraint and at least 1 more implicit constraint.
4. Generate a new response to your prompt from ResponseBot, and generate feedback from FeedbackBot. If FeedbackBot thinks your prompt is sufficient, move on to the next challenge. If not, keep tweaking the prompt and generating a response from both bots until FeedbackBot considers your prompt to be fully satisfactory.

💡 It's important that you keep generating responses to your prompt, even if it seems redundant. The point of this exercise is to observe how adding constraints changes the model's output as it further tailors the response to the user. These are the situations we want to prepare the model for in the real world!

Click here to generate a response from ResponseBot

Click here to generate feedback from FeedbackBot

### Challenge #2 - Layered instruction following

Instructions are not the same thing as constraints, although they may seem similar. An instruction tells the model what to do, and a constraint restricts the way in which a model should follow an instruction or set of instructions. Using the example from the previous question:

* "Give me 5 recipes for homemade meatloaf. Each recipe should be low in sodium."

We can see that "Give me 5 recipes for homemade meatloaf" is an instruction, and "Each recipe should be low in sodium" is a constraint that applies to that instruction. When writing prompts that have both constraints and multiple instructions, it's usually best to be clear about which of the instructions the constraint applies to. For example, if we modify the prompt to be:

* "Give me 5 recipes for homemade meatloaf. Each recipe should be low in sodium. Also, tell me the proper way to clean my utensils after handling raw meat."

It's clear that the constraint "Each recipe should be low in sodium" just applies to "Give me 5 recipes for homemade meatloaf". So, breaking down the prompt, we have 3 components:

1. "Give me 5 recipes for homemade meatloaf" = **instruction**
2. "Each recipe should be low in sodium" = **constraint** that applies to "Give me 5 recipes for homemade meatloaf"
3. "Tell me the proper way to clean my utensils after handling raw meat" = **instruction**

Now, consider an alternative version of the prompt:

* "Give me 5 recipes for homemade meatloaf. Each recipe should be low in sodium. Also, tell me how to make homemade pizza with mozzarella."

Explanation: With this prompt, it isn't 100% clear on whether the constraint "Each recipe should be low in sodium" applies to the pizza too or just the meatloaf. Although it would be best for the model to consider the sodium constraint when giving its pizza recipe, we don't want to penalize a response for instruction following due to an unclear prompt. A better version would be:

* "Give me 5 recipes for homemade meatloaf along with a recipe for homemade pizza with mozzarella. All recipes should be low in sodium."

Explanation: This prompt is essentially asking the same thing, but it's clear now that the pizza should be low in sodium too. We can confidently penalize a response that ignores the sodium constraint.

When creating prompts with multiple instructions, it's helpful to consider how those instructions relate to each other. Are the instructions independent of one another? Or are they dependent? Let's look at some examples for both:

* Dependent: "**Give me 5 recipes for homemade meatloaf.** Each recipe should be low in sodium. **At the end of every recipe, give me a list of the ingredients used and tell me whether I can buy them online or not.**"

  + Why is this dependent? If the model doesn't satisfy the first instruction (providing 5 recipes), it can't fully satisfy the second instruction (listing the ingredients at the end of the recipe). It could, however, satisfy the first instruction without satisfying the second.
* Independent: "**Give me 5 recipes for homemade meatloaf.** Each recipe should be low in sodium. **Also, tell me the proper way to clean my utensils after handling raw meat.**"

  + Why is this independent? There's no connection between giving recipes for meatloaf and describing how to clean utensils. It's possible for the model to satisfy only the first instruction, only the second instruction, both, or neither.
* Both dependent and independent: "**Give me 5 recipes for homemade meatloaf.** Each recipe should be low in sodium. **At the end of every recipe, give me a list of the ingredients used and tell me whether I can buy them online or not. Also, tell me the proper way to clean my utensils after handling raw meat.**"

  + Combining the previous two examples gives us a prompt with both dependent and independent instructions. The instruction "At the end of every recipe, give me a list of the ingredients used and tell me whether I can buy them online or not" is still dependent on "Give me 5 recipes for homemade meatloaf", but "Tell me the proper way to clean my utensils after handling raw meat" is independent of both.

It's even possible to have multiple layers of dependency! Take a look at the following example:

* "**Give me 5 recipes for homemade meatloaf. At the end of every recipe, give me a list of the ingredients used and tell me whether I can easily order them online or not. For the ones that can easily be ordered, estimate whether buying online would be cheaper than buying in a store, more expensive, or about the same."**

Explanation: Fulfilling the second instruction - "At the end of every recipe, give me a list of the ingredients used and tell me whether I can easily order them online or not**" -**is dependent on fulfilling the first instruction "Give me 5 recipes for homemade meatloaf**".**Fulfillingthe third instruction - "For the ones that can easily be ordered, estimate whether buying online would be cheaper than buying in a store, more expensive, or about the same" - is similarly dependent on fulfilling the second instruction (and therefore the first instruction too). Basically, if the model doesn't provide the 5 meatloaf recipes, it won't really be able to satisfy any of the instructions given in the prompt.

#### Your challenge: Write a natural sounding prompt with 5 instructions. You may add constraints too if you like, but they aren't needed for this challenge. Structure the prompt as follows:

* Instruction #1 - base instruction

  + Instruction #2 - dependent on Instruction #1

    - Instruction #3 - dependent on Instruction #2
  + Instruction #4 - dependent on Instruction #1
* Instruction #5 - independent of all others

#### The content of the prompt should fall under the category Learning new skills.

Process:

1. Start off by writing Instruction #1, Instruction #2, and Instruction #5. So you should have 3 instructions total - one of which is dependent on the first instruction, and the other of which is independent of the first instruction, similar to the "Both" example above.

   📄 Note that you aren't actually including the phrases "Instruction #1", "Instruction #2", etc. in your prompt - this labeling system is just to help you understand the prompt's structure. The prompt should sound natural!
2. Then, generate a response from ResponseBot and read through it. Once you've done that, add Instruction #3 and Instruction #4, bringing the total number of instructions to 5.

   📢 Keep in mind that the requirements for Instructions #3 and #4 are different! Instruction #3 should have nested dependency, meaning it depends on Instruction #2. Instruction #4, on the other hand, is a separate instruction that depends only on Instruction #1.
3. Generate a new response to your prompt from ResponseBot, and generate feedback from FeedbackBot. If FeedbackBot thinks your prompt is sufficient, move on to the next challenge. If not, keep tweaking the prompt and generating a response from both bots until FeedbackBot considers your prompt to be fully satisfactory.

   📄 Note that FeedbackBot may have trouble deciphering the nested dependencies correctly. If you get stuck after a few tries and you believe that the bot keeps making mistakes, feel free to move on.

💡 It's important that you keep generating responses to your prompt, even if it seems redundant. The point of this exercise is to observe how adding instructions changes the model's output as it further tailors the response to the user. These are the situations we want to prepare the model for in the real world!

Click here to generate a response from ResponseBot

Click here to generate a response from FeedbackBot

### Challenge #3 - Reasoning

Reasoning is one of the most important emerging abilities for LLMs. And it's perhaps the one that depends most heavily on human training! That's where you come in. When we say "reasoning" in relation to LLMs, we're talking about the ability to form connections between different pieces of information as opposed to just regurgitating knowledge. Basically, if you could Google your prompt and get an exact answer from a search result, that's not a reasoning prompt.

Reasoning is necessary for many word problem style prompts, such as this one:

1. "Guests at a party are given either a red, blue, yellow, or green hat. There is at least 1 of each hat color. The guests are then seated at a circular round table, such that everyone is next to 2 other people. No two people with green hats are seated next to each other. Everyone with a red hat is seated next to exactly one other person wearing a red hat. Everyone with a blue hat is seated next to exactly 1 person with a green hat and 1 person with a yellow hat. Everyone with a yellow hat is between 2 people with the same hat color. What's the fewest number of guests needed to guarantee an equal distribution of hat colors?"

Reasoning is often necessary to solve STEM and coding prompts, but it can apply in other areas too. For example:

2. "I'm a first time homebuyer and I'm working with a realtor to find something suitable for my needs. I want 3 bedrooms, 2 baths, a fireplace, a nice sized yard, and space in the living room for a big TV. The realtor is showing me a lot of houses that don't have enough bedrooms, don't have fireplaces, and don't have big yards. They all seem to have 2 baths and space for the TV, though. Why do you think that is? I never mentioned prioritizing my needs in any particular order."
3. "I have a small statue that lost one of its legs and keeps on falling over. I need it to stay standing up though because if I lay it down on the ground someone might trip over it. The only materials I have to work with right now are yarn, rope, duct tape, and nails. The only tool I have is a hammer. How can I keep the statue propped up for now until I get it repaired?"

Some prompts may appear to rely on reasoning, but in reality they can fairly easily be converted into a regurgitation style prompt. Consider the following examples:

4. "I'm trying to grow vegetables, but sometimes I come outside and I see the vegetables all chewed up and on the ground. There's a 3 foot fence around them with netting, so whatever's doing it must be either coming from the air, climbing, or jumping over the fence. What animals could be responsible? I live in the Pacific Southwest btw."
5. "I am trying to learn oil painting by making copies of other paintings, but a lot of mine don't have the same level of fine detail, and the color contrast seems off even though I've been matching each color I use to the ones used in the original copy. What do you think I'm doing wrong?"
6. "My friend always seems to overpay for properties in Monopoly, yet he keeps on winning. Do you think he's getting lucky or is there some type of strategy here?"

These three prompts can essentially be rewritten as:

7. "What are Pacific Southwest animals that eat vegetables and can fly, climb, or jump high?"
8. "What are common mistakes in oil painting that lead to lack of fine detail and poor color contrast?"
9. "Is overpaying for properties a rational strategy in Monopoly?"

These prompts could likely be answered using one or two search results. This doesn't mean that they are bad prompts! They just aren't relying on a heavy amount of reasoning. Prompts 4, 5, and 6 are still preferable to prompts 7, 8, and 9 because of the added personalization. Real users will often present models with simple questions hidden inside extra text, and it's the model's responsibility to distinguish between the two.

On the other hand, prompts 1, 2, and 3 cannot easily be converted into a regurgitation prompt. Prompt 1 is a word problem, and prompts 2 and 3 are too specific to be answered using only general information. If you search "How to prop up a one legged statue using rope, yarn, nails, duct tape, and a hammer?" on Google, you are unlikely to get a match tailored to all of those things.

It's important to remember that some reasonings prompts leave room for subjectivity, and there may be projects on the platform where this isn't desired. Always pay attention to your project's specific instructions.

#### Your challenge: Write a prompt that requires the model to use reasoning. There is no category for this prompt; you may use any topic you choose. Word problems, puzzles, and riddles are acceptable. Feel free to get creative!

Process:

1. First, write your reasoning prompt.
2. Then, try rewriting your prompt as a regurgitation style prompt. If you find yourself easily able to do so, modify the prompt.
3. Repeat this process until you feel the prompt requires a satisfactory amount of reasoning.
4. Generate a new response to your prompt from ResponseBot, and generate feedback from FeedbackBot. If FeedbackBot thinks your prompt is sufficient, move on to the next challenge. If not, keep tweaking the prompt and generating a response from both bots until FeedbackBot considers your prompt to be fully satisfactory.

Click here to generate a response from ResponseBot

Click here to generate feedback from FeedbackBot

### Challenge #4 - Images

Some projects on the platform may require you to upload an image and write a prompt based on that image. For example:

> What type of dog is this?

![File:Papillon-dog-agility.jpg](https://upload.wikimedia.org/wikipedia/commons/thumb/f/f2/Papillon-dog-agility.jpg/125px-Papillon-dog-agility.jpg)

Generally for these types of projects, you'll want to create a prompt that **requires the model to view the image**. Otherwise, the image isn't necessary.

Good prompts:

✅ "Describe the location of the dog relative to the ground."

✅ "How many bars are visible in the image, and do they all have a blue stripe?"

✅ "The fence in this picture is 5 feet tall. Do you think that's tall enough, or will my dog be able to get out?"

Bad prompts:

❌ "Are papillon dogs good at jumping?"

❌ "The image shows a dog jumping over three bars. Is it common for dogs to do activities like that?"

❌ "The fence in this picture is 5 feet tall. Do you think that's tall enough, or will my **papillon** dog be able to get out?"

These three prompts are bad because they don't require the model to actually view the image. The first question, "Are papillon dogs good at jumping?" can be answered just by a Google search. The third prompt is basically just asking "Can papillon dogs jump over a 5 foot fence?", so the image is similarly irrelevant. The second question gives away the content of the image, which is not correct.

📝 Note that the prompt "The fence in this picture is 5 feet tall. Do you think that's tall enough, or will my dog be able to get out?" is acceptable because the model still needs to view the image to determine what kind of dog the user has. Some dogs can jump that high, and some can't.

#### Your challenge: Write a prompt that requires the model to answer a question based on an image.

Process:

1. Choose an image to use from [Openverse](https://openverse.org/). Please filter the results as shown below to only include images with Public Domain or CC0 licensing.

   ![](https://d3j6doxkchhi5i.cloudfront.net/project-text-images/879f5d4c-c5ff-4e96-b77a-2e951a2928cd.png)
2. Upload the direct URL to your image in the field below.

   📌 To get the direct URL: right click on the image and hit "Open Image in New Tab." This should create a new tab showing **only** the image (not the rest of the website). Copy the link from this tab and paste it into the Image URL field.

   📌 For example, the direct URL for [this image](https://openverse.org/image/118131cd-08fa-4846-bd16-ae2af9432d24?q=mountain&p=6) is <https://live.staticflickr.com/8522/8468633942_3541dcbb15_b.jpg>.

   📌 Please only use .jpg, .jpeg, or .png files.
3. Write a prompt that requires the model to view the image. For example, you could ask the model to identify something in the image, to describe what it sees in the image, or to determine the location of items in the image relative to one another.
4. Generate a response to your prompt from ResponseBot and generate feedback from FeedbackBot. If FeedbackBot thinks your prompt relies on the image, move on to the next challenge. If not, keep tweaking the prompt and generating a response from both bots until FeedbackBot considers your prompt to be fully satisfactory.

Please upload your image URL below.

Click here to generate a response from ResponseBot.

❗If the model fails to respond, check to make sure that:

1. Your **first** response field contains the prompt and the **second** response field contains the image - not the other way around!
2. Your image URL ends with .jpg, .jpeg, or .png. If it doesn't, then either your image is the wrong file type or your URL is for the Openverse page hosting the image, not the direct link to the image itself.

Click here to generate feedback from FeedbackBot

### Challenge #5 - Putting it all together

For the last challenge, choose 2 of the 4 categories from above to combine for your prompt. You will then build your prompt iteratively and test it against 3 different models to see how they respond.

Adding natural constraints

Layered instruction following

Reasoning

Images

*Optional Comments - feedback about the task. Did you find it helpful? What would you like to see improved?*

Last draft saved at 1:40 PM

Expires in: 364 days 22 hours



[$255.00](https://app.dataannotation.tech/workers/payments)

---

[Code of Conduct](https://docs.google.com/document/u/1/d/e/2PACX-1vQ3pmQsDlC3_aA4zcV1g3Bd9-KYrGPg9Z37FMt0C8UdBObA5qAa9f36uEDAtXtT_NCecyqKAH6xD7UZ/pub) [Support](https://app.dataannotation.tech/workers/support)

© 2026 DataAnnotation. All rights reserved.